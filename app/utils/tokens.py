import math
from typing import Dict, Any, List

#  ~1 token ≈ 4 caractères 
def _count_text_tokens(txt: str) -> int:
    if not txt:
        return 0
    words = txt.split()
    by_words = len(words)
    by_chars = math.ceil(len(txt) / 4)
    return max(by_words, by_chars)

def count_message_tokens(msg: Dict[str, Any]) -> int:
    total = 0
    for p in (msg.get("parts") or []):
        total += _count_text_tokens(str(p.get("text", "")))
    return total + 3

def count_contents_tokens(contents: List[Dict[str, Any]]) -> int:
    return sum(count_message_tokens(m) for m in contents)
