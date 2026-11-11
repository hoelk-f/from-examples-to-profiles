def transform(x: str) -> str:
    import re
    m = re.search(r'#\S+', x)
    return m.group(0) if m else ''