def transform(x: str) -> str:
    parts = x.strip().split()
    return parts[0] if parts else ""