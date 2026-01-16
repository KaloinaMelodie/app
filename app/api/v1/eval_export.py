# app/routes/eval_export.py
# API d’export des fichiers d’entrée d’évaluation à partir de Hive (sans chunk).
# - POST /eval/export/docs-metadata  -> data/eval/docs_metadata.csv
# - POST /eval/export/qrels          -> data/eval/qrels_queries.csv
#
# Adapte l'import des fonctions Hive selon ton projet.

import os
import re
import csv
from collections import defaultdict
from typing import Any, List, Dict, Optional

from fastapi import APIRouter, HTTPException, Query

from app.services.hive_service import  (
    fetch_surveys_with_content,
    fetch_consoles_with_content,
    fetch_pages_with_content,
    fetch_documents_with_content,
)

router = APIRouter(prefix="/eval/export", tags=["eval-export"])

DATA_DIR = "D:/2M/assistant/full/app/app/eval/data"
os.makedirs(DATA_DIR, exist_ok=True)

# ---------------------------
# Détection (ville / année / thème)
# ---------------------------
CITY_WORDS = [
    "Antananarivo", "Toamasina", "Mahajanga", "Fianarantsoa",
    "Toliara", "Antsirabe", "Antsiranana", "Ambatondrazaka"
]
CITY_WORDS_LO = [c.lower() for c in CITY_WORDS]
YEAR_RE = re.compile(r"(20\d{2})")

THEME_KEYWORDS = {
    "qualite_eau": ["qualité de l'eau", "qualite de l eau", "water quality", "kalitaon-drano"],
    "handwashing": ["handwashing", "lavage des mains", "fanasana tanana"],
    "coverage": ["couverture", "coverage", "water access", "tahan'ny fidirana", "tahan ny fidirana"],
    "chlorination": ["chlorination", "chloration", "résiduel", "residual", "klôro", "klo ro"],
    "sop": ["sop", "procédure", "procedure", "torolalana", "guide", "training", "formation"]
}

def _norm(x: Any) -> str:
    if isinstance(x, str):
        return x.strip()
    if x is None:
        return ""
    return str(x).strip()

def _listify(x) -> List[str]:
    if x is None:
        return []
    if isinstance(x, list):
        return [_norm(t) for t in x if _norm(t)]
    return [_norm(x)]

def detect_city(text: str) -> str:
    t = (text or "").lower()
    for c in CITY_WORDS_LO:
        if c in t:
            return c
    return ""

def detect_year(text: str) -> str:
    m = YEAR_RE.search(text or "")
    return m.group(1) if m else ""

def detect_theme(text: str) -> str:
    t = (text or "").lower()
    for theme, kws in THEME_KEYWORDS.items():
        for kw in kws:
            if kw in t:
                return theme
    return ""

def to_tags(city: str, year: str, theme: str, extra: List[str]) -> str:
    tags = []
    if theme: tags.append(theme)
    if city: tags.append(city)
    if year: tags.append(year)
    for x in extra or []:
        x = _norm(x)
        if x and x not in tags:
            tags.append(x)
    return ";".join(tags)

# ---------------------------
# 1) Export docs_metadata.csv
# ---------------------------
@router.post("/docs-metadata")
def export_docs_metadata(limit: int = Query(10, ge=1, le=10000)) -> Dict[str, Any]:
    """
    Construit data/eval/docs_metadata.csv depuis Hive (sans chunk).
    - surveys/consoles/documents: utilisent `nom` (titre), `langue`, `emplacement`
    - pages: utilisent `title`, `url`, `breadcrumbs`
    """ 
    # Récupération Hive
    surveys   = fetch_surveys_with_content()     # SurveyItem
    consoles  = fetch_consoles_with_content()    # ConsoleItem
    documents = fetch_documents_with_content()   # DocumentItem
    pages     = fetch_pages_with_content()       # PageItem

    rows: List[Dict[str, str]] = []

    def is_url(s: str) -> bool:
        s = (s or "").lower().strip()
        return s.startswith("http://") or s.startswith("https://")

    def push_row_doclike(item: Any, source_type: str):
        did   = _norm(getattr(item, "id", None))
        title = _norm(getattr(item, "nom", None))
        lang  = _norm(getattr(item, "langue", None)).lower()
        empl  = _listify(getattr(item, "emplacement", None))
        if not did or not title:
            return
        extra = [e for e in empl if not is_url(e)]
        city  = detect_city(title)
        year  = detect_year(title)
        theme = detect_theme(title)
        tags  = to_tags(city, year, theme, extra)

        url = ""
        if source_type in ("survey"):
            url = f"https://portal.mwater.co/#/forms/{did}"
        if source_type in ("console"):
            url = f"https://portal.mwater.co/#/consoles/{did}"
        if source_type in ("document"):
            url = f"https://portal.mwater.co/#/documents/{did}"

        rows.append({
            "doc_id": did,
            "title": title,
            "source_type": source_type,
            "lang": lang if lang in ("fr","en","mg") else "",
            "tags": tags,
            "url_or_path": url
        })

    def push_row_page(item: Any):
        did   = _norm(getattr(item, "id", None))
        title = _norm(getattr(item, "title", None))
        url   = _norm(getattr(item, "url", None))
        crumbs = _listify(getattr(item, "breadcrumbs", None))
        if not did or not title:
            return
        city  = detect_city(title)
        year  = detect_year(title)
        theme = detect_theme(title)
        tags  = to_tags(city, year, theme, crumbs)
        rows.append({
            "doc_id": did,
            "title": title,
            "source_type": "page",
            "lang": "",
            "tags": tags,
            "url_or_path": url
        })

    for it in surveys:   push_row_doclike(it, "survey")
    for it in consoles:  push_row_doclike(it, "console")
    for it in documents: push_row_doclike(it, "document")
    for it in pages:     push_row_page(it)

    # dédup par doc_id
    seen = set()
    uniq_rows = []
    for r in rows:
        if r["doc_id"] in seen:
            continue
        seen.add(r["doc_id"])
        uniq_rows.append(r)

    out_csv = os.path.join(DATA_DIR, "docs_metadata.csv")
    with open(out_csv, "w", encoding="utf-8-sig", newline="") as f:  # <-- utf-8-sig pour Excel
        w = csv.DictWriter(f, fieldnames=["doc_id","title","source_type","lang","tags","url_or_path"])
        w.writeheader()
        w.writerows(uniq_rows)

    return {"status": "ok", "count": len(uniq_rows), "path": out_csv}

# ---------------------------
# 2) Export qrels_queries.csv
# ---------------------------
@router.post("/qrels")
def export_qrels_queries(
    min_per_city: int = Query(1, ge=1),
    min_per_theme: int = Query(1, ge=1),
) -> Dict[str, Any]:
    """
    Construit data/eval/qrels_queries.csv à partir de data/eval/docs_metadata.csv.
    Génère des queries EASY / MEDIUM / HARD + hard negatives (proches mais non pertinents),
    et ajoute un Fallback DOC-TITLE pour garantir ≥ 1 requête par document.
    """
    import pandas as pd
    from collections import defaultdict

    docs_csv = os.path.join(DATA_DIR, "docs_metadata.csv")
    if not os.path.exists(docs_csv):
        raise HTTPException(status_code=400, detail="docs_metadata.csv introuvable. Appelle d'abord /eval/export/docs-metadata")

    # Lecture robuste (sans NaN) + normalisation langue
    docs_df = pd.read_csv(docs_csv, keep_default_na=False, na_filter=False)
    # S'assure que ces colonnes existent (au cas où)
    for col in ["doc_id", "title", "source_type", "lang"]:
        if col not in docs_df.columns:
            docs_df[col] = ""
    # Normaliser lang en str minuscule
    docs_df["lang"] = docs_df["lang"].astype(str).str.strip().str.lower()
    # Filtrage de base
    docs_df = docs_df[docs_df["doc_id"].astype(str).str.len() > 0]
    docs_df = docs_df[docs_df["title"].astype(str).str.len() > 0]

    # Passage en liste de dicts
    docs = docs_df.to_dict(orient="records")

    # ---------------------------
    # Index (ville / thème / année)
    # ---------------------------
    by_city:  Dict[str, List[str]] = defaultdict(list)
    by_theme: Dict[str, List[str]] = defaultdict(list)
    by_year:  Dict[str, List[str]] = defaultdict(list)

    for d in docs:
        did   = d["doc_id"]
        title = d["title"]
        city  = detect_city(title)
        year  = detect_year(title)
        theme = detect_theme(title)
        if city:  by_city[city].append(did)
        if theme: by_theme[theme].append(did)
        if year:  by_year[year].append(did)

    # ---------------------------
    # Helpers
    # ---------------------------
    def qid(i: int) -> str:
        return f"Q{i:04d}"

    def lang_majoritaire(doc_ids: List[str]) -> str:
        langs = []
        for x in doc_ids:
            vals = docs_df.loc[docs_df["doc_id"] == x, "lang"]
            if not vals.empty:
                v = str(vals.values[0]).strip().lower()
                if v in ("fr", "en", "mg"):
                    langs.append(v)
        for l in ("fr", "en", "mg"):
            if l in langs:
                return l
        return "fr"

    def pick_hard_neg(
        target_city: str, target_theme: str, target_year: str,
        avoid: List[str], k: int = 2
    ) -> List[str]:
        cands: List[str] = []
        if target_city and target_city in by_city:
            cands += [x for x in by_city[target_city] if x not in avoid]
        if target_theme and target_theme in by_theme:
            cands += [x for x in by_theme[target_theme] if x not in avoid]
        if target_year and target_year in by_year:
            cands += [x for x in by_year[target_year] if x not in avoid]
        out, seen = [], set()
        for x in cands:
            if x in seen or x in avoid:
                continue
            seen.add(x); out.append(x)
            if len(out) >= k:
                break
        return out

    def pick_negatives_same_type(doc_id: str, source_type: str, avoid: List[str], k: int = 3) -> List[str]:
        pool = docs_df[docs_df["source_type"] == source_type]["doc_id"].tolist()
        out: List[str] = []
        for did2 in pool:
            if did2 in avoid or did2 == doc_id:
                continue
            out.append(did2)
            if len(out) >= k:
                break
        return out

    def base_label_for_theme(theme: str, lang: str, capitalize: bool = False) -> str:
        fr = {
            "qualite_eau": "qualité de l’eau",
            "handwashing": "lavage des mains",
            "coverage": "couverture en eau potable",
            "chlorination": "chloration résiduelle",
            "sop": "procédures SOP",
        }
        en = {
            "qualite_eau": "water quality",
            "handwashing": "handwashing",
            "coverage": "water access coverage",
            "chlorination": "chlorination residual",
            "sop": "SOP procedures",
        }
        t = theme.replace("_", " ")
        if lang == "fr":
            label = fr.get(theme, t)
            return label.capitalize() if capitalize else label
        if lang == "en":
            label = en.get(theme, t)
            return label.capitalize() if capitalize else label
        # mg : fallback simple
        return t

    # ---------------------------
    # Génération des requêtes
    # ---------------------------
    queries: List[Dict[str, str]] = []
    i = 1
    covered_doc_ids: set[str] = set()

    # 1) EASY — ville + année + thème → 1 pertinent + ~2 HN
    for d in docs:
        did    = d["doc_id"]
        title  = d["title"]
        lang_v = str(d.get("lang", "")).strip().lower()
        lang   = lang_v if lang_v in ("fr", "en", "mg") else "fr"
        city   = detect_city(title)
        year   = detect_year(title)
        theme  = detect_theme(title)
        if not (city and year and theme):
            continue

        base = base_label_for_theme(theme, lang, capitalize=False)
        if lang == "fr":
            qtxt = f"{base} {year} {city}"
        elif lang == "en":
            qtxt = f"{base} {city} {year}"
        else:
            qtxt = f"{base} {city} {year}"

        queries.append({
            "query_id": qid(i),
            "query_text": qtxt,
            "query_lang": lang,
            "difficulty": "easy",
            "relevant_doc_ids": did,
            "hard_negative_ids": ";".join(pick_hard_neg(city, theme, year, [did], k=2)),
            "notes": f"EASY: ville+année+thème d'après le titre: {title}",
        })
        i += 1
        covered_doc_ids.add(did)

    # 2) MEDIUM — ville + thème (sans année) → plusieurs pertinents + 2 HN
    for city, doc_ids in by_city.items():
        if len(doc_ids) < max(1, min_per_city):
            continue
        # thèmes rencontrés pour cette ville
        city_themes = set()
        for _did in doc_ids:
            t = docs_df.loc[docs_df["doc_id"] == _did, "title"].values[0]
            th = detect_theme(t)
            if th:
                city_themes.add(th)
        for theme in list(city_themes)[:2]:  # max 2 thèmes / ville
            rels = list(dict.fromkeys(doc_ids))[:3]
            lang = lang_majoritaire(rels)
            base = base_label_for_theme(theme, lang, capitalize=False)
            if lang == "fr":
                qtxt = f"{base} {city}"
            elif lang == "en":
                qtxt = f"{base} in {city}"
            else:
                qtxt = f"{base} {city}"

            queries.append({
                "query_id": qid(i),
                "query_text": qtxt,
                "query_lang": lang,
                "difficulty": "medium",
                "relevant_doc_ids": ";".join(rels),
                "hard_negative_ids": ";".join(pick_hard_neg(city, theme, "", rels, k=2)),
                "notes": f"MEDIUM: ville+thème; rels={rels}",
            })
            i += 1
            for _did in rels:
                covered_doc_ids.add(_did)

    # 3) HARD — générique par thème → 3 pertinents + 3 HN
    for theme, doc_ids in by_theme.items():
        if len(doc_ids) < max(1, min_per_theme):
            continue
        rels = list(dict.fromkeys(doc_ids))[:3]
        lang = lang_majoritaire(rels)
        base = base_label_for_theme(theme, lang, capitalize=True)
        qtxt = base  # requête générique

        queries.append({
            "query_id": qid(i),
            "query_text": qtxt,
            "query_lang": lang,
            "difficulty": "hard",
            "relevant_doc_ids": ";".join(rels),
            "hard_negative_ids": ";".join(pick_hard_neg("", theme, "", rels, k=3)),
            "notes": f"HARD: générique par thème; rels={rels}",
        })
        i += 1
        for _did in rels:
            covered_doc_ids.add(_did)

    # 4) FALLBACK — garantir ≥ 1 requête par document (DOC-TITLE)
    for d in docs:
        did = d["doc_id"]
        if did in covered_doc_ids:
            continue
        title       = d["title"]
        lang_val    = str(d.get("lang", "")).strip().lower()
        lang        = lang_val if lang_val in ("fr", "en", "mg") else "fr"
        source_type = d.get("source_type", "")

        queries.append({
            "query_id": qid(i),
            "query_text": title,  # requête = titre brut
            "query_lang": lang,
            "difficulty": "medium",
            "relevant_doc_ids": did,
            "hard_negative_ids": ";".join(
                pick_negatives_same_type(did, source_type, [did], k=3)
            ),
            "notes": "MEDIUM (fallback): requête basée sur le titre exact",
        })
        i += 1

    # ---------------------------
    # Écriture CSV (UTF-8 BOM)
    # ---------------------------
    out_csv = os.path.join(DATA_DIR, "qrels_queries.csv")
    with open(out_csv, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "query_id","query_text","query_lang","difficulty",
            "relevant_doc_ids","hard_negative_ids","notes"
        ])
        w.writeheader()
        w.writerows(queries)

    return {"status": "ok", "count": len(queries), "path": out_csv}
