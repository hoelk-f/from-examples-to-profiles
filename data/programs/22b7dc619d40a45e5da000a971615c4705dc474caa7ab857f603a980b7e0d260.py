def transform(x: str) -> str:
    import re
    m = re.match(r'\d+', x.lstrip())
    return m.group(0) if m else ""