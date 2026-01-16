# mgmerl_eval/eval_common.py
from typing import List, Dict, Tuple
import numpy as np

def precision_at_k(rels: List[int], k: int) -> float:
    return float(np.mean(rels[:k])) if rels else 0.0

def recall_at_k(rels: List[int], k: int, n_relevant: int) -> float:
    if n_relevant <= 0: 
        return 0.0
    return float(np.sum(rels[:k]) / n_relevant)

def dcg_at_k(gains: List[float], k: int) -> float:
    gains = np.array(gains[:k], dtype=float)
    if gains.size == 0:
        return 0.0
    discounts = 1.0 / np.log2(np.arange(2, gains.size + 2))
    return float(np.sum(gains * discounts))

def ndcg_at_k(rels: List[int], k: int) -> float:
    dcg = dcg_at_k(rels, k)
    ideal = sorted(rels, reverse=True)
    idcg = dcg_at_k(ideal, k)
    return float(dcg / idcg) if idcg > 0 else 0.0

def mrr(rels: List[int]) -> float:
    for i, r in enumerate(rels, start=1):
        if r == 1:
            return 1.0 / i
    return 0.0

def compute_metrics_for_query(binary_rels: List[int], k: int = 10) -> Dict[str, float]:
    return {
        "P@10": precision_at_k(binary_rels, k),
        "R@10": recall_at_k(binary_rels, k, int(sum(binary_rels))),  # approximation: nb rels trouvés
        "nDCG@10": ndcg_at_k(binary_rels, k),
        "MRR": mrr(binary_rels),
    }
