def transform(x: str) -> str:
    parts = x.split(',')
    if len(parts) > 3:
        return parts[3].strip()
    return ''