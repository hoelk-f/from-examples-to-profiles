def transform(x: str) -> str:
    import re
    m = re.search(r'[-+]?\d*\.?\d+', x)
    return m.group(0) if m else ""