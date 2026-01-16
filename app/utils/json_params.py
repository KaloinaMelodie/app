from __future__ import annotations
import json
from typing import Any, Dict, List, Tuple

def _parse_json_param(raw: str | None, default: Any) -> Any:
    if raw is None or raw == "":
        return default
    try:
        return json.loads(raw)
    except Exception:
        return default

def parse_selector(raw: str | None) -> Dict[str, Any]:
    sel = _parse_json_param(raw, {})
    return sel if isinstance(sel, dict) else {}

def parse_fields(raw: str | None) -> Dict[str, int] | None:
    f = _parse_json_param(raw, None)
    if isinstance(f, dict):
        proj = {}
        for k, v in f.items():
            proj[str(k)] = 1 if v else 0
        return proj
    return None

def parse_sort(raw: str | None) -> List[Tuple[str, int]]:
    s = _parse_json_param(raw, [])
    out: List[Tuple[str, int]] = []
    if isinstance(s, list):
        for item in s:
            if isinstance(item, list) and len(item) >= 1:
                field = str(item[0])
                order = -1 if (len(item) >= 2 and str(item[1]).lower() in ("desc", "-1")) else 1
                out.append((field, order))
            elif isinstance(item, str):
                out.append((item, 1))
    return out

def parse_limit(raw: str | None, default: int = 100, max_limit: int = 1000) -> int:
    try:
        val = int(raw) if raw is not None else default
    except Exception:
        val = default
    return max(1, min(val, max_limit))

import numpy as np

def to_jsonable(x):
    if isinstance(x, np.ndarray):
        return x.astype(float).tolist()
    if isinstance(x, (np.floating,)):
        return float(x)
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (bytes, bytearray)):
        return x.decode('utf-8', errors='ignore')
    if isinstance(x, (list, tuple)):
        return [to_jsonable(v) for v in x]
    if isinstance(x, dict):
        return {k: to_jsonable(v) for k, v in x.items()}
    return x