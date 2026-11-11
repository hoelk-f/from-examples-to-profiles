def transform(x: str) -> str:
    parts = x.split(',')
    if len(parts) >= 2:
        return parts[1].strip()
    return ''