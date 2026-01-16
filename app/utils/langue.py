from __future__ import annotations
from typing import Tuple, Dict
import re
from langid.langid import LanguageIdentifier, model
from typing import Optional
import os
import logging

try:
    from google.cloud import translate_v3 as translate  
except Exception:
    translate = None

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# normaliser proba
_IDENTIFIER = LanguageIdentifier.from_modelstring(model, norm_probs=True)
_IDENTIFIER.set_languages(['mg', 'fr', 'en'])

def _normalize_text(t: str) -> str:
    t = (t or "").strip().lower()
    t = t.replace("’", "'").replace("\u200b", "")
    t = re.sub(r"\s+", " ", t)
    return t

def _rank_probs(text: str) -> Dict[str, float]:
    t = _normalize_text(text)
    if not t:
        return {'mg': 0.0, 'fr': 0.0, 'en': 0.0}
    if len(t) < 4:
        return {'mg': 1/3, 'fr': 1/3, 'en': 1/3}

    ranked = _IDENTIFIER.rank(t)  
    out = {k: float(v) for k, v in ranked if k in ('mg', 'fr', 'en')}
    s = sum(out.values()) or 1.0
    for k in ('mg', 'fr', 'en'):
        out[k] = out.get(k, 0.0) / s
    return out

def detect_dominant_lang(text: str) -> Tuple[str, float]:
    probs = _rank_probs(text)  
    if not any(probs.values()):
        return ("und", 0.0)
    lang = max(probs.items(), key=lambda kv: kv[1])[0]
    conf = float(probs[lang])
    # Si le texte est trop court et que les proba sont quasi uniformes, return 'und'
    if len(_normalize_text(text)) < 4 and conf < 0.40:
        return ("und", conf)
    return (lang, conf)

def detect_lang_distribution(text: str) -> Dict[str, float]:
    return _rank_probs(text)


# def should_translate_to_fr(lang: str, conf: float, text: str) -> bool:
def should_translate_to_fr(text: str) -> bool:
    t = _normalize_text(text)
    if not t or len(t) < 8:
        return False

    # if rang 'mg' is 0 or 1
    probs = detect_lang_distribution(text) 
    ranking = sorted(probs.items(), key=lambda kv: kv[1], reverse=True)
    mg_rank = next((i for i, (k, _) in enumerate(ranking) if k == 'mg'), None)
    return mg_rank is not None and mg_rank <= 1
    
    # # 0.70 à 0.80
    # return bool(t and len(t) >= 8 and lang == "mg" and conf >= 0.70)

def translate_to_fr_if_malagasy(text: str, project_id: Optional[str] = os.getenv("GCP_PROJECT_ID")) -> str:
    should_translate = should_translate_to_fr(text)

    if not should_translate:
        return text

    if not translate:
        return text

    if not project_id:
        return text

    logger.info("Traduction MG->FR")
    client = translate.TranslationServiceClient()
    parent = f"projects/{project_id}/locations/global"
    resp = client.translate_text(
        contents=[text],
        target_language_code="fr",
        source_language_code="mg",
        parent=parent,
        mime_type="text/plain",
    )
    for tr in resp.translations:
        if tr.translated_text:
            return tr.translated_text
    return text