def transform(x: str) -> str:
    import re
    months = ("January|February|March|April|May|June|July|August|September|October|November|December")
    m = re.search(rf"\b({months})\b", x)
    if not m:
        return ""
    return x[m.start():].strip()