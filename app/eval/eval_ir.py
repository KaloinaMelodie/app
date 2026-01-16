# mgmerl_eval/eval_ir.py
"""
Évalue des runs (classements) contre un qrels (ground truth).
Mode: --mode runs (fichiers CSV runs_* générés par l'API)
Sorties: aggregate_metrics.csv, per_query_metrics.csv, et PNG (P@10, R@10, nDCG@10, MRR)
"""

import argparse, os, csv
from typing import Dict, List
import pandas as pd
import matplotlib.pyplot as plt

from eval_common import compute_metrics_for_query

def load_qrels(qrels_csv: str) -> Dict[str, List[str]]:
    qrels = {}
    df = pd.read_csv(qrels_csv, keep_default_na=False, na_filter=False)
    for _, row in df.iterrows():
        qid = str(row["query_id"])
        # relevant_doc_ids peut être "a;b;c" ou "a"
        rels = str(row["relevant_doc_ids"]).split(";") if str(row["relevant_doc_ids"]) else []
        qrels[qid] = [r.strip() for r in rels if r.strip()]
    return qrels

def load_runs(runs_csv: str) -> Dict[str, List[str]]:
    runs = {}
    df = pd.read_csv(runs_csv, keep_default_na=False, na_filter=False)
    # on s'assure tri par (query_id, rank)
    df = df.sort_values(by=["query_id", "rank"])
    for qid, grp in df.groupby("query_id"):
        runs[str(qid)] = [str(did) for did in grp["doc_id"].tolist()]
    return runs

def aggregate_and_save(per_query: List[Dict[str, any]], out_dir: str, model_name: str):
    agg = {}
    if per_query:
        keys = ["P@10","R@10","nDCG@10","MRR"]
        for k in keys:
            agg[k] = sum([x[k] for x in per_query]) / len(per_query)
    agg_df = pd.DataFrame([{"model": model_name, **agg}])
    agg_df.to_csv(os.path.join(out_dir, "aggregate_metrics.csv"), index=False)
    pd.DataFrame(per_query).to_csv(os.path.join(out_dir, "per_query_metrics.csv"), index=False)

    # bar plots
    plt.figure()
    plt.bar([model_name], [agg.get("P@10", 0.0)])
    plt.title("P@10")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "P@10_by_model.png"), dpi=160)
    plt.close()

    plt.figure()
    plt.bar([model_name], [agg.get("R@10", 0.0)])
    plt.title("R@10")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "R@10_by_model.png"), dpi=160)
    plt.close()

    plt.figure()
    plt.bar([model_name], [agg.get("nDCG@10", 0.0)])
    plt.title("nDCG@10")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "nDCG@10_by_model.png"), dpi=160)
    plt.close()

    plt.figure()
    plt.bar([model_name], [agg.get("MRR", 0.0)])
    plt.title("MRR")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "MRR_by_model.png"), dpi=160)
    plt.close()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--mode", choices=["runs"], default="runs")
    ap.add_argument("--runs-csv", required=True)
    ap.add_argument("--model-name", default=None)
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    qrels_csv = os.path.join(args.data_dir, "qrels_queries.csv")
    if not os.path.exists(qrels_csv):
        raise FileNotFoundError("qrels_queries.csv non trouvé dans --data-dir")

    qrels = load_qrels(qrels_csv)
    runs  = load_runs(args.runs_csv)

    model_name = args.model_name or os.path.splitext(os.path.basename(args.runs_csv))[0]
    per_query = []

    missing = 0
    for qid, positives in qrels.items():
        ranked = runs.get(qid, [])
        if not ranked:
            missing += 1
        # binaire: 1 si doc_id dans positives
        rels_bin = [1 if did in positives else 0 for did in ranked]
        m = compute_metrics_for_query(rels_bin, k=10)
        per_query.append({"query_id": qid, **m})

    if missing > 0:
        print(f"[WARN] {missing} query_id sans rangs dans {args.runs_csv}")

    aggregate_and_save(per_query, args.out_dir, model_name)

if __name__ == "__main__":
    main()
