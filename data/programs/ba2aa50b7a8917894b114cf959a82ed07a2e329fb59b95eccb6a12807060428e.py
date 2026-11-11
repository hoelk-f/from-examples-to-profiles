def transform(x: str) -> str:
    parts = [p.strip() for p in x.split(',')]
    return parts[1] if len(parts) > 1 else ""