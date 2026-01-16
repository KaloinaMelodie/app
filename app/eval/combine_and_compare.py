# mgmerl_eval/combine_and_compare.py
"""
Combine 2+ résultats 'aggregate_metrics.csv' et 2+ 'per_query_metrics.csv'
pour produire des comparaisons mxbai vs gemini (barres et scatter par requête).
"""

import argparse, os
import pandas as pd
import matplotlib.pyplot as plt

def load_agg(path):
    df = pd.read_csv(path)
    # on attend une colonne 'model'
    base = os.path.splitext(os.path.basename(path))[0]
    if "model" not in df.columns:
        df["model"] = base
    return df

def load_per(path, label):
    df = pd.read_csv(path)
    df["model"] = label
    return df

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", required=True, help="chemins vers aggregate_metrics.csv (>=2)")
    ap.add_argument("--per-query", nargs="+", required=True, help="chemins vers per_query_metrics.csv (>=2)")
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    # agrégés
    aggs = [load_agg(p) for p in args.runs]
    agg_all = pd.concat(aggs, ignore_index=True)
    agg_all.to_csv(os.path.join(args.out_dir, "aggregate_metrics_all.csv"), index=False)

    # barres comparatives
    for metric in ["P@10","R@10","nDCG@10","MRR"]:
        plt.figure()
        plt.bar(agg_all["model"], agg_all[metric])
        plt.title(metric)
        plt.tight_layout()
        plt.savefig(os.path.join(args.out_dir, f"{metric}_compare.png"), dpi=160)
        plt.close()

    # per-query
    if len(args.per_query) >= 2:
        labels = []
        per_list = []
        for p in args.per_query:
            label = os.path.basename(os.path.dirname(p)) or os.path.splitext(os.path.basename(p))[0]
            labels.append(label)
            per_list.append(load_per(p, label))
        merged = per_list[0]
        for df in per_list[1:]:
            merged = pd.merge(merged, df, on="query_id", suffixes=("", "_alt"))
        merged.to_csv(os.path.join(args.out_dir, "per_query_merged.csv"), index=False)

        # scatter nDCG@10 (modèle A vs B)
        if "nDCG@10" in merged.columns and "nDCG@10_alt" in merged.columns:
            plt.figure()
            plt.scatter(merged["nDCG@10"], merged["nDCG@10_alt"], s=10)
            plt.xlabel(labels[0] + " nDCG@10")
            plt.ylabel(labels[1] + " nDCG@10")
            plt.title("nDCG@10 par requête")
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(os.path.join(args.out_dir, "scatter_nDCG10.png"), dpi=160)
            plt.close()

if __name__ == "__main__":
    main()
