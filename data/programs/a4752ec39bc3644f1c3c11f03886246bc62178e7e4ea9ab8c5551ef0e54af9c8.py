def transform(x: str) -> str:
    import re
    m = re.search(r'^\s*\d+\.\s*(.*?)\s*,\s*\$', x)
    if m:
        return m.group(1).strip()
    # Fallback handling if pattern doesn't match
    s = re.sub(r'^\s*\d+\.\s*', '', x)
    return s.split(',', 1)[0].strip()