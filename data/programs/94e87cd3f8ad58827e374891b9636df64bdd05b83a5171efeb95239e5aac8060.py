def transform(x: str) -> str:
    parts = x.split('.', 2)
    return parts[2] if len(parts) > 2 else ''