from __future__ import annotations
import hashlib
import tiktoken
import re
from typing import Any, Dict, Iterable, List


def clean_string_list(l):
    if isinstance(l, list):
        return [s.strip('"') for s in l if isinstance(s, str)]
    return l

def clean_milvus_results(raw_results: list) -> list:
        cleaned = []
        for result_group in raw_results:
            for item in result_group:
                try:
                    cleaned_item = {
                        "id": item.get("id"),
                        "score": float(item.get("distance")),
                        **item.get("entity", {})  # déstructure les champs de 'entity'
                    }
                    cleaned.append(cleaned_item)
                except Exception as e:
                    print("Erreur lors du nettoyage d'un item Milvus:", e)
        return cleaned

# un encoding proche de celui de ton modèle (ici on prend cl100k_base, très courant)
encoding = tiktoken.get_encoding("cl100k_base")

def split_into_chunks(text, max_tokens=500, overlap=100):
    # Étape 1 : découper en phrases
    sentences = re.split(r'(?<=[.?!])\s+', text.strip())
    
    chunks = []
    current_chunk = []
    current_tokens = 0

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        token_count = len(encoding.encode(sentence))

        # Si ajout de cette phrase dépasse max_tokens
        if current_tokens + token_count > max_tokens:
            chunk_text = " ".join(current_chunk).strip()
            if chunk_text:
                chunks.append(chunk_text)
            
            # Overlap : on garde les dernières phrases
            overlap_tokens = 0
            overlap_chunk = []
            for s in reversed(current_chunk):
                s_tokens = len(encoding.encode(s))
                if overlap_tokens + s_tokens <= overlap:
                    overlap_chunk.insert(0, s)
                    overlap_tokens += s_tokens
                else:
                    break
            
            current_chunk = overlap_chunk.copy()
            current_tokens = sum(len(encoding.encode(s)) for s in current_chunk)

        # Ajouter la phrase en cours
        current_chunk.append(sentence)
        current_tokens += token_count

    # Ajouter le dernier chunk
    if current_chunk:
        chunk_text = " ".join(current_chunk).strip()
        if chunk_text:
            chunks.append(chunk_text)

    return chunks



def md5_hex(parts: Iterable[str]) -> str:
    m = hashlib.md5()
    for p in parts:
        m.update(p.encode("utf-8"))
    return m.hexdigest()

def utf8_truncate(text: str, max_bytes: int) -> str:
        if not isinstance(text, str):
            text = str(text) if text is not None else ""
        b = text.encode("utf-8")
        if len(b) <= max_bytes:
            return text
        b = b[:max_bytes]
        while b and (b[-1] & 0xC0) == 0x80:  
            b = b[:-1]
        return b.decode("utf-8", "ignore")
    


def _item_url(it):
    if isinstance(it, dict):
        return it.get("url")
    return it

def _merge_media(dst_list: List[dict], new_items: Iterable[Any]) -> None:
    seen = { _item_url(x) for x in dst_list if _item_url(x) }
    for it in new_items or []:
        u = _item_url(it)
        if u and u not in seen:
            dst_list.append(it)
            seen.add(u)

def group_training_metadata(search_results: List[Dict[str, Any]], limit_per_media: int | None = None):
    grouped: Dict[str, Dict[str, Any]] = {}

    for hit in search_results or []:
        doc_id = hit.get("doc_id")
        if not doc_id:
            continue

        g = grouped.setdefault(doc_id, {
            "doc_id": doc_id,
            "url": None,
            "breadcrumbs": [],
            "images": [],
            "gifs": [],
            "videos": [],
        })

        if not g["url"] and hit.get("url"):
            g["url"] = hit["url"]

        b = hit.get("breadcrumbs") or []
        if isinstance(b, list) and len(b) > len(g["breadcrumbs"]):
            g["breadcrumbs"] = b

        _merge_media(g["images"], hit.get("images"))
        _merge_media(g["gifs"], hit.get("gifs"))
        _merge_media(g["videos"], hit.get("videos"))

    metas = list(grouped.values())

    if limit_per_media is not None and limit_per_media > 0:
        for m in metas:
            m["images"] = m["images"][:limit_per_media]
            m["gifs"]   = m["gifs"][:limit_per_media]
            m["videos"] = m["videos"][:limit_per_media]

    return metas
