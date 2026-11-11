def transform(x: str) -> str:
    import re
    m = re.search(r'\((\d+)', x)
    return m.group(1) if m else ""