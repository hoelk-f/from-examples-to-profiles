def transform(x: str) -> str:
    import re
    m = re.search(r'\b(\d{4})\b', x)
    return m.group(1)