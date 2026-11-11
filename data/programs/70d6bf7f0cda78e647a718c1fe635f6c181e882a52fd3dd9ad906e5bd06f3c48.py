def transform(x: str) -> str:
    import re
    m = re.search(r'\(([^;]*);', x)
    if m:
        return m.group(1).strip()
    m = re.search(r'\(([^)]*)\)', x)
    if m:
        return m.group(1).strip()
    return ""