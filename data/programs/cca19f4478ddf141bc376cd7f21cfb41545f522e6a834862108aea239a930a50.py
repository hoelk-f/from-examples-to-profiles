def transform(x: str) -> str:
    parts = x.split()
    return parts[1] if len(parts) > 1 else ""