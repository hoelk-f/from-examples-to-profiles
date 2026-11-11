def transform(x: str) -> str:
    import re
    words = re.findall(r"[A-Za-z']+", x)
    return words[-1] if words else ""