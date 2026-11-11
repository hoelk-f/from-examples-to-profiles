def transform(x: str) -> str:
    import re
    m = re.search(r'About\s+([\d,]+)\s+results', x)
    if m:
        return m.group(1)
    # fallback: first token after "About"
    parts = x.split()
    if len(parts) > 1:
        return parts[1]
    return ""