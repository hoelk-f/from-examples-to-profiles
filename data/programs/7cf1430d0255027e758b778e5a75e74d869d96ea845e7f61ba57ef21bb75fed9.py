def transform(x: str) -> str:
    parts = [p.strip() for p in x.split(',')]
    if len(parts) >= 2:
        return ', '.join(parts[-2:])
    return x.strip()
