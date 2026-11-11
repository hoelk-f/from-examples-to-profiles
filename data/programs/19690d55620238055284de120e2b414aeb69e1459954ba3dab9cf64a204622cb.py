def transform(x: str) -> str:
    parts = x.split(',')
    if len(parts) < 3:
        return ''
    return parts[2].strip()