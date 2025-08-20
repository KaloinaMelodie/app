from fastapi import APIRouter, HTTPException, Body,Query
import os, json, re, hashlib
from google.cloud import translate_v3 as translate
from typing import Any, Dict, List, Tuple
import logging
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


DO_NOT_TRANSLATE = {"MGMERL"}  # ajoute tes marques/termes

ROOT = Path(__file__).resolve().parents[3] 
LOCALES_DIR = Path(os.getenv("LOCALES_DIR", ROOT / "locales"))


def hash_fr(value: Any) -> str:
    """Hash pour détecter si la source FR a changé (clé “stale”)."""
    if isinstance(value, (dict, list)):
        src = json.dumps(value, ensure_ascii=False, sort_keys=True)
    else:
        src = str(value)
    return hashlib.sha1(src.encode("utf-8")).hexdigest()

def freeze_tokens(s: str) -> Tuple[str, List[str]]:
    """Protège {{vars}}, balises <0>…</0>, et termes interdits de traduction."""
    tokens = []
    def repl(m):
        tokens.append(m.group(0))
        return f"__PH_{len(tokens)-1}__"
    # {{var}} et {var} ICU simple
    out = re.sub(r"(\{\{[^}]+\}\}|\{[^}]+\})", repl, s)
    # balises Markdown/JSX-like <0>…</0> ou <b>…</b>
    out = re.sub(r"(</?[\w0-9]+[^>]*>)", repl, out)
    # termes interdits
    for term in DO_NOT_TRANSLATE:
        out = out.replace(term, f"__TERM_{term}__")
    return out, tokens

def thaw_tokens(s: str, tokens: List[str]) -> str:
    for i, tok in enumerate(tokens):
        s = s.replace(f"__PH_{i}__", tok)
    for term in DO_NOT_TRANSLATE:
        s = s.replace(f"__TERM_{term}__", term)
    return s

def g_translate(texts: List[str], target: str, source: str) -> List[str]:
    if not texts:
        return []
    client = translate.TranslationServiceClient()
    parent = f"projects/{os.getenv('GCP_PROJECT_ID')}/locations/{os.getenv('GCP_TRANSLATE_LOCATION','global')}"
    resp = client.translate_text(
        contents=texts, mime_type="text/plain",
        source_language_code=source, target_language_code=target,
        parent=parent,
    )
    return [t.translated_text for t in resp.translations]

def translate_string(value: str, target: str, source: str) -> str:
    frozen, toks = freeze_tokens(value)
    out = g_translate([frozen], target, source)[0]
    return thaw_tokens(out, toks)

def deep_merge_translate(fr_obj: Any, tgt_obj: Any, target: str, source: str, mode: str, report: dict):
    """
    mode: 'missing' -> traduit uniquement les clés absentes ou vides
          'all'     -> retraduit toutes les chaînes (écrase)
    report: collecte ce qui a été créé/mis à jour
    """
    if isinstance(fr_obj, dict):
        out = {} if not isinstance(tgt_obj, dict) else dict(tgt_obj)
        for k, v in fr_obj.items():
            cur = tgt_obj.get(k) if isinstance(tgt_obj, dict) else None
            out[k] = deep_merge_translate(v, cur, target, source, mode, report)
        return out

    if isinstance(fr_obj, list):
        # On traduit élément par élément si ce sont des chaînes.
        if all(isinstance(x, str) for x in fr_obj):
            # garde cible s’il existe en list, sinon traduit tout
            if isinstance(tgt_obj, list) and len(tgt_obj) == len(fr_obj) and mode == "missing":
                return tgt_obj
            translated = [translate_string(x, target, source) for x in fr_obj]
            report["translated_count"] += len(translated)
            return translated
        # récursif sinon
        res = []
        tgt_list = tgt_obj if isinstance(tgt_obj, list) else [None]*len(fr_obj)
        for i, v in enumerate(fr_obj):
            res.append(deep_merge_translate(v, tgt_list[i] if i < len(tgt_list) else None, target, source, mode, report))
        return res

    if isinstance(fr_obj, str):
        if mode == "missing":
            if isinstance(tgt_obj, str) and tgt_obj.strip():
                return tgt_obj  # garde la trad existante
            translated = translate_string(fr_obj, target, source)
            report["translated_count"] += 1
            return translated
        else:  # mode == "all"
            translated = translate_string(fr_obj, target, source)
            report["translated_count"] += 1
            return translated

    # types non string (nombre, bool…), on recopie
    return tgt_obj if tgt_obj is not None else fr_obj

translate_router = APIRouter()

@translate_router.post("/i18n/translate")
def translate_namespaces(payload: dict):
    """
    Body:
    {
      "namespaces": ["common","topbar"],  // si vide -> tous les fichiers dans locales/fr
      "from": "fr",
      "to": ["en","mg"],
      "mode": "missing" | "all",          // défaut: missing
      "dry_run": false                    // si true: n’écrit pas, renvoie juste le report
    }
    """
    logger.info(f"Received translation request: {payload}")
    ns_list = payload.get("namespaces") or []
    src = payload.get("from") or "fr"
    targets = payload.get("to") or ["en","mg"]
    mode = payload.get("mode") or "missing"
    dry_run = bool(payload.get("dry_run", False))

    src_dir = LOCALES_DIR / src
    if not src_dir.exists():
        return JSONResponse({"error":"source locale not found"}, status_code=400)

    # si namespaces non fournis, prends tous les *.json de la source
    if not ns_list:
        ns_list = [p.stem for p in src_dir.glob("*.json")]

    summary = []
    for ns in ns_list:
        src_path = src_dir / f"{ns}.json"
        if not src_path.exists():
            continue
        with open(src_path, "r", encoding="utf-8") as f:
            fr_json = json.load(f)

        for tgt in targets:
            tgt_dir = LOCALES_DIR / tgt
            tgt_dir.mkdir(parents=True, exist_ok=True)
            tgt_path = tgt_dir / f"{ns}.json"
            tgt_json = {}
            if tgt_path.exists():
                with open(tgt_path, "r", encoding="utf-8") as f:
                    tgt_json = json.load(f)

            report = {"namespace": ns, "target": tgt, "translated_count": 0}
            merged = deep_merge_translate(fr_json, tgt_json, tgt, src, mode, report)

            if not dry_run:
                with open(tgt_path, "w", encoding="utf-8") as f:
                    json.dump(merged, f, ensure_ascii=False, indent=2)

            summary.append({**report, "path": str(tgt_path)})

    return {"ok": True, "mode": mode, "dry_run": dry_run, "changes": summary}
