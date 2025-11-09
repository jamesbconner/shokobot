import re
from typing import List

_PIPE_SPLIT = re.compile(r"\s*\|\s*")
_BBCODE_TAG = re.compile(r"\[(\/?)(i|b|u|spoiler|quote|code)\]", re.IGNORECASE)

def split_pipe(s: str | None) -> List[str]:
    if not s:
        return []
    parts = [p.strip() for p in _PIPE_SPLIT.split(s) if p.strip()]
    seen, out = set(), []
    for p in parts:
        if p.lower() in seen:
            continue
        seen.add(p.lower())
        out.append(p)
    return out

def clean_description(desc: str | None) -> str:
    if not desc:
        return ""
    text = _BBCODE_TAG.sub("", desc)
    text = re.sub(r"[ \t]+", " ", text).strip()
    return text
