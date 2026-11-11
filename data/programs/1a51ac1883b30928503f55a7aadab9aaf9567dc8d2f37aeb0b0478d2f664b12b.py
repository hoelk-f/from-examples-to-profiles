def transform(x: str) -> str:
    parts = [p for p in x.split('.') if p]
    return '.'.join(parts[:2])