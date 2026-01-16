from __future__ import annotations
from typing import Any, Dict, Tuple, Set

# chg:champs in doc where doc.val != base.val
# rem: champ in base not in doc
def diff_fields(base: Dict[str, Any], doc: Dict[str, Any]) -> Tuple[Set[str], Set[str]]:
    changed: Set[str] = set()
    removed: Set[str] = set()
    base_keys = set(base.keys())
    doc_keys = set(doc.keys())

    for k in doc_keys:
        if k == "_id":
            continue
        if k not in base or base.get(k) != doc.get(k):
            changed.add(k)
    for k in (base_keys - doc_keys):
        if k != "_id":
            removed.add(k)
    return changed, removed


def three_way_merge(base: Dict[str, Any], doc: Dict[str, Any], current: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
    merged = dict(current) if current else {}
    conflicted = False

    changed, removed = diff_fields(base or {}, doc or {})

    # Apply changed
    for k in changed:
        base_val = (base or {}).get(k, "__<absent>__")
        curr_val = (current or {}).get(k, "__<absent>__")
        new_val  = doc.get(k)
        if curr_val == base_val:
            merged[k] = new_val
        else:
            conflicted = True

    for k in removed:
        base_val = (base or {}).get(k, "__<absent>__")
        curr_val = (current or {}).get(k, "__<absent>__")
        if curr_val == base_val:
            if k in merged:
                del merged[k]
        else:
            conflicted = True

    return merged, conflicted
