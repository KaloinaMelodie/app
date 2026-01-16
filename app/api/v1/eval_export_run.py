# app/routes/eval_export_runs.py
# Génère des "runs" (classements) pour l'évaluation IR à partir de qrels_queries.csv
# en interrogeant Milvus via hybrid_search (vector_title + vector) avec le bon modèle.
#
# Endpoints:
#   POST /eval/export/runs
#   GET  /eval/export/debug/one
#   GET  /eval/export/debug/check-docid

import os
import csv
from typing import List, Dict, Any, Optional

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

# === Services Milvus ===
# mxbai (1024 dims) -> search_collection (docs/consoles/surveys), formation_collection (pages)
from app.services.milvus_service import MilvusService
# gemini (768 dims) -> search_multilingual_collection, formation_multilingual_collection
from app.services.milvus_multilingual_service import MilvusMultilingualService

# === Embedders ===
# ⚠️ ADAPTE si besoin (selon où sont tes fonctions)
from app.agents.embedder import generate_embedding as embed_mxbai
from app.agents.embedder import generate_embedding_gemini as embed_gemini

# Milvus hybrid
from pymilvus import AnnSearchRequest
from pymilvus import WeightedRanker

router = APIRouter(prefix="/eval/export", tags=["eval-export"])
DATA_DIR = "D:/2M/assistant/full/app/app/eval/data"
os.makedirs(DATA_DIR, exist_ok=True)


# ---------------------------
# Sélection service/collection
# ---------------------------
def pick_service_and_collection(model: str, corpus: str):
    """
    Retourne (service, collection_name) en fonction du modèle et du corpus:
      - mxbai  : search_collection / formation_collection   (MilvusService)
      - gemini : search_multilingual_collection / formation_multilingual_collection (MilvusMultilingualService)
    """
    model = (model or "").lower().strip()
    corpus = (corpus or "").lower().strip()

    if model not in ("mxbai", "gemini"):
        raise HTTPException(status_code=400, detail="Paramètre 'model' invalide (mxbai|gemini)")

    if corpus not in ("search", "formation"):
        raise HTTPException(status_code=400, detail="Paramètre 'corpus' invalide (search|formation)")

    if model == "mxbai":
        svc = MilvusService()
        if corpus == "search":
            coll = getattr(svc, "collection_name", "search_collection")
        else:
            coll = getattr(svc, "formation_collection_name", "formation_collection")
        return svc, coll

    # model == "gemini"
    svc = MilvusMultilingualService()
    if corpus == "search":
        coll = getattr(svc, "collection_name", "search_multilingual_collection")
    else:
        coll = getattr(svc, "formation_collection_name", "formation_multilingual_collection")
    return svc, coll


# ---------------------------
# Embedding de requête
# ---------------------------
def embed_query_text(model: str, text: str) -> List[float]:
    model = (model or "").lower().strip()
    if model == "mxbai":
        return embed_mxbai(text)
    if model == "gemini":
        return embed_gemini(text)
    raise ValueError("model must be 'mxbai' or 'gemini'")


# ---------------------------
# Hybrid search d'évaluation
# ---------------------------
def hybrid_search_eval(
    svc,
    collection_name: str,
    qvec: List[float],
    top_k: int,
    min_score: float,
) -> List[Dict[str, Any]]:
    """
    Lance une hybrid_search (vector_title + vector) avec WeightedRanker(0.8,0.3).
    - Pas de filtre d'accès
    - On NE DEMANDE PAS 'score' en output_fields (n'existe pas en champ)
    - On lit la note via clean_milvus_results(...) ou fallback (distance/score)
    """
    req1 = AnnSearchRequest(data=[qvec], anns_field="vector_title", param={}, limit=top_k)
    req2 = AnnSearchRequest(data=[qvec], anns_field="vector",       param={}, limit=top_k)
    rerank = WeightedRanker(0.8, 0.3)

    res = svc.client.hybrid_search(
        collection_name=collection_name,
        reqs=[req1, req2],
        ranker=rerank,
        limit=top_k,
        search_params={"metric_type": "COSINE"},
        partition_names=[],
        group_by_field="doc_id",
        group_size=2,
        output_fields=["doc_id"],  # surtout pas 'score' (ce n'est pas un champ)
    )

    # Tente d'utiliser ton utilitaire interne si disponible
    rows: List[Dict[str, Any]] = []
    try:
        from app.utils import clean_milvus_results
        rows = clean_milvus_results(res)  # attendu: liste de dicts avec 'doc_id' et 'score'
    except Exception:
        # Fallback robuste
        def get_attr(obj, name, default=None):
            return obj.get(name) if hasattr(obj, "get") else getattr(obj, name, default)

        for r in res:
            did = get_attr(r, "doc_id", "")
            if not did:
                continue
            # distance (Milvus) ou score (selon wrapper)
            dist = get_attr(r, "distance", None)
            sc = get_attr(r, "score", None)
            score_val = None
            if sc is not None:
                score_val = float(sc)
            elif dist is not None:
                # Pour COSINE récent, c'est souvent la similarité (plus haut = mieux)
                score_val = float(dist)
            else:
                score_val = 0.0
            rows.append({"doc_id": str(did).strip(), "score": score_val})

    # Filtrage + tri
    ranked = [ {"doc_id": x["doc_id"], "score": float(x.get("score", 0.0)) } for x in rows if x.get("doc_id") ]
    ranked = [ x for x in ranked if x["score"] >= min_score ]
    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked[:top_k]


# ===========================================================
#                    ENDPOINTS PRINCIPAUX
# ===========================================================
router = APIRouter(prefix="/eval/export", tags=["eval-export"])


@router.post("/runs")
def export_runs(
    model: str  = Query(..., regex="^(mxbai|gemini)$"),
    corpus: str = Query(..., regex="^(search|formation)$"),
    top_k: int = Query(10, ge=1, le=50),
    min_score: float = Query(0.0),
    strict_doc_filter: bool = Query(True, description="Si True, garde uniquement les doc_id présents dans docs_metadata pour le corpus."),
) -> Dict[str, Any]:
    """
    Génère data/eval/runs_{model}_{corpus}.csv à partir de qrels_queries.csv.
    - Embedding requête dans l'espace du modèle choisi.
    - Recherche dans la collection du corpus choisi.
    - Filtre optionnel strict_doc_filter pour diagnostiquer les mismatches.
    """
    qrels_csv = os.path.join(DATA_DIR, "qrels_queries.csv")
    docs_csv  = os.path.join(DATA_DIR, "docs_metadata.csv")

    if not (os.path.exists(qrels_csv) and os.path.exists(docs_csv)):
        raise HTTPException(status_code=400, detail="qrels_queries.csv ou docs_metadata.csv manquant.")

    qrels_df = pd.read_csv(qrels_csv, keep_default_na=False, na_filter=False)
    docs_df  = pd.read_csv(docs_csv,  keep_default_na=False, na_filter=False)

    # borne le corpus: search => survey/console/document ; formation => page
    allowed_types = ["page"] if corpus == "formation" else ["survey", "console", "document"]
    doc_ids_ok = set(docs_df[docs_df["source_type"].isin(allowed_types)]["doc_id"].astype(str))

    svc, collection_name = pick_service_and_collection(model, corpus)

    out_rows: List[Dict[str, Any]] = []

    for _, row in qrels_df.iterrows():
        qid   = str(row["query_id"])
        qtext = str(row["query_text"])

        # 1) Embedding requête
        try:
            qvec = embed_query_text(model, qtext)
        except Exception as e:
            print(f"[WARN] embedding failed for {qid}: {e}")
            continue

        # 2) Recherche hybride d'évaluation
        try:
            ranked = hybrid_search_eval(svc, collection_name, qvec, top_k, min_score)
        except Exception as e:
            print(f"[WARN] search failed for {qid}: {e}")
            continue

        # 3) Filtre 'doc_ids_ok' si demandé
        rank = 1
        for it in ranked:
            did = it["doc_id"]
            if strict_doc_filter and did not in doc_ids_ok:
                # log utile pour diagnostiquer le corpus/ID
                print(f"[FILTER] drop {did} (absent de docs_metadata pour corpus={corpus})")
                continue
            out_rows.append({"query_id": qid, "doc_id": did, "rank": rank, "score": it["score"]})
            rank += 1
            if rank > top_k:
                break

    if not out_rows:
        raise HTTPException(
            status_code=500,
            detail=f"Aucun résultat (model={model}, corpus={corpus}). "
                   f"Essayez strict_doc_filter=false pour diagnostiquer les doc_id renvoyés par Milvus."
        )

    out_csv = os.path.join(DATA_DIR, f"runs_{model}_{corpus}.csv")
    with open(out_csv, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["query_id","doc_id","rank","score"])
        w.writeheader()
        w.writerows(out_rows)

    return {"status": "ok", "count": len(out_rows), "path": out_csv}


# ===========================================================
#                       ENDPOINTS DEBUG
# ===========================================================

@router.get("/debug/one")
def debug_one(
    query_id: str,
    model: str  = Query(..., regex="^(mxbai|gemini)$"),
    corpus: str = Query(..., regex="^(search|formation)$"),
    top_k: int = 10,
):
    """
    Debug: renvoie les top_k résultats bruts (doc_id, score) pour un query_id donné,
    et indique si chaque doc_id est présent dans docs_metadata pour le corpus.
    """
    qrels_csv = os.path.join(DATA_DIR, "qrels_queries.csv")
    docs_csv  = os.path.join(DATA_DIR, "docs_metadata.csv")
    if not (os.path.exists(qrels_csv) and os.path.exists(docs_csv)):
        raise HTTPException(status_code=400, detail="qrels_queries.csv ou docs_metadata.csv manquant.")

    qrels_df = pd.read_csv(qrels_csv, keep_default_na=False, na_filter=False)
    docs_df  = pd.read_csv(docs_csv,  keep_default_na=False, na_filter=False)

    row = qrels_df[qrels_df["query_id"] == query_id]
    if row.empty:
        raise HTTPException(status_code=404, detail="query_id introuvable dans qrels_queries.csv")

    qtext = str(row.iloc[0]["query_text"])

    svc, collection_name = pick_service_and_collection(model, corpus)
    qvec = embed_query_text(model, qtext)
    ranked = hybrid_search_eval(svc, collection_name, qvec, top_k=top_k, min_score=0.0)

    allowed_types = ["page"] if corpus == "formation" else ["survey", "console", "document"]
    doc_ids_ok = set(docs_df[docs_df["source_type"].isin(allowed_types)]["doc_id"].astype(str))

    for r in ranked:
        r["in_docs_metadata"] = r["doc_id"] in doc_ids_ok

    return {"query_text": qtext, "collection": collection_name, "results": ranked}


@router.get("/debug/check-docid")
def debug_check_docid(
    doc_id: str,
    model: str  = Query(..., regex="^(mxbai|gemini)$"),
    corpus: str = Query(..., regex="^(search|formation)$"),
):
    """
    Debug: vérifie si un doc_id est présent dans docs_metadata (pour le corpus).
    NB: La présence exacte dans Milvus n'est pas triviale sans helper de listing;
        ici on retourne 'unknown' pour Milvus, sauf si tu as un helper.
    """
    docs_csv  = os.path.join(DATA_DIR, "docs_metadata.csv")
    if not os.path.exists(docs_csv):
        raise HTTPException(status_code=400, detail="docs_metadata.csv manquant.")

    docs_df  = pd.read_csv(docs_csv,  keep_default_na=False, na_filter=False)
    allowed_types = ["page"] if corpus == "formation" else ["survey", "console", "document"]
    in_docs_csv = str(doc_id) in set(docs_df[docs_df["source_type"].isin(allowed_types)]["doc_id"].astype(str))

    # Placeholder: si tu as un helper pour vérifier l'existence dans Milvus, branche-le ici
    in_milvus = "unknown"

    svc, collection_name = pick_service_and_collection(model, corpus)

    return {
        "doc_id": doc_id,
        "corpus": corpus,
        "model": model,
        "collection": collection_name,
        "in_docs_metadata": in_docs_csv,
        "in_milvus": in_milvus
    }
