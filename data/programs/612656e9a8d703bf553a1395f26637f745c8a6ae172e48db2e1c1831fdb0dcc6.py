def transform(x: str) -> str:
    import re
    m = re.search(r'\d+(?:\.\d+)?[A-Za-z]+', x)
    return m.group(0) if m else ""