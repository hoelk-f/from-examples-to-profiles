def transform(x: str) -> str:
    import re
    m = re.search(r'#\w+', x)
    return m.group(0) if m else ''