def transform(x: str) -> str:
    parts = x.split()
    return parts[5] if len(parts) > 5 else ""