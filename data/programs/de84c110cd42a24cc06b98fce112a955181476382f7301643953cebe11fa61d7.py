def transform(x: str) -> str:
    import re
    m = re.search(r'Model:\s*(\S+)', x)
    if m:
        return m.group(1)
    parts = x.strip().split()
    return parts[-1] if parts else ""