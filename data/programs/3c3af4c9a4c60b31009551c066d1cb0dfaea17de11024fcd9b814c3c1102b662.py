def transform(x: str) -> str:
    parts = [p.strip() for p in x.split(',')]
    return parts[-2] if len(parts) >= 2 else ''