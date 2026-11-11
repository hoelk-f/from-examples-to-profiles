def transform(x: str) -> str:
    parts = x.split(',')
    return parts[2].strip() if len(parts) > 2 else ""