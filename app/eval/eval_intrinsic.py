# mgmerl_eval/eval_intrinsic.py
"""
Intrinsic metrics for embedding spaces.

Inputs (per model) — CSV with:
  - doc_id
  - (optional) label columns: source_type, lang, tag_group
  - vector_* columns: the embedding dimensions (vector_0, vector_1, ...)

Usage:
  python mgmerl_eval/eval_intrinsic.py --emb-csv data/eval/embeddings_mxbai.csv --out-dir outputs/intrinsic_mxbai
  python mgmerl_eval/eval_intrinsic.py --emb-csv data/eval/embeddings_gemini.csv --out-dir outputs/intrinsic_gemini --umap 1
"""
import argparse, os, json
from typing import List, Tuple
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
from sklearn.neighbors import NearestNeighbors

def load_vectors(df: pd.DataFrame) -> Tuple[np.ndarray, List[str]]:
    vec_cols = [c for c in df.columns if c.startswith("vector_")]
    if not vec_cols:
        raise ValueError("No columns starting with 'vector_' found.")
    X = df[vec_cols].to_numpy(dtype=np.float32)
    return X, vec_cols

def compute_isotropy(X: np.ndarray, n_dirs: int = 128, seed: int = 0) -> float:
    rng = np.random.RandomState(seed)
    means = []
    for _ in range(n_dirs):
        v = rng.randn(X.shape[1]).astype(np.float32)
        v /= (np.linalg.norm(v) + 1e-12)
        means.append(float(np.mean(X @ v)))
    return float(np.std(np.array(means)))  # lower is more isotropic

def compute_hubness(X: np.ndarray, k: int = 10) -> float:
    k = min(k, len(X))
    nbrs = NearestNeighbors(n_neighbors=k, metric="cosine").fit(X)
    _, indices = nbrs.kneighbors(X)
    counts = np.zeros(len(X), dtype=np.int32)
    for row in indices:
        for idx in row:
            counts[idx] += 1
    m = counts.mean()
    s = counts.std() + 1e-12
    skew = np.mean(((counts - m) / s) ** 3)  # Fisher-Pearson skewness
    return float(skew)

def try_umap_plot(df: pd.DataFrame, X: np.ndarray, out_path: str, color_col: str = "lang"):
    try:
        import umap
        reducer = umap.UMAP(n_neighbors=15, min_dist=0.1, random_state=42)
        X2 = reducer.fit_transform(X)
        plt.figure()
        if color_col in df.columns:
            labels = df[color_col].astype(str).values
            uniq = sorted(set(labels))
            for u in uniq:
                mask = labels == u
                plt.scatter(X2[mask, 0], X2[mask, 1], s=8, label=u)
            plt.legend()
        else:
            plt.scatter(X2[:, 0], X2[:, 1], s=6)
        plt.title("UMAP 2D")
        plt.tight_layout()
        plt.savefig(out_path, dpi=160)
        plt.close()
    except Exception:
        print("UMAP not installed or failed; skipping 2D plot. (pip install umap-learn)")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--emb-csv", required=True, dest="emb_csv")
    ap.add_argument("--out-dir", required=True, dest="out_dir")
    ap.add_argument("--label-col", default="lang", dest="label_col")
    ap.add_argument("--umap", type=int, default=0, dest="use_umap")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    df = pd.read_csv(args.emb_csv)
    X, vec_cols = load_vectors(df)

    norms = np.linalg.norm(X, axis=1)
    iso = compute_isotropy(X)
    hub = compute_hubness(X, k=min(10, len(X)))

    sil = dbi = chi = None
    if args.label_col in df.columns and len(set(df[args.label_col].astype(str))) >= 2:
        labels = df[args.label_col].astype(str).values
        sil = float(silhouette_score(X, labels, metric="cosine"))
        dbi = float(davies_bouldin_score(X, labels))
        chi = float(calinski_harabasz_score(X, labels))

    summary = {
        "n_vectors": int(X.shape[0]),
        "dim": int(X.shape[1]),
        "norm_mean": float(norms.mean()),
        "norm_std": float(norms.std()),
        "isotropy_std": float(iso),
        "hubness_skew": float(hub),
        "silhouette_cosine": sil,
        "davies_bouldin": dbi,
        "calinski_harabasz": chi
    }
    with open(os.path.join(args.out_dir, "intrinsic_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    if args.use_umap == 1:
        try_umap_plot(df, X, os.path.join(args.out_dir, "umap_2d.png"), color_col=args.label_col)

if __name__ == "__main__":
    main()
