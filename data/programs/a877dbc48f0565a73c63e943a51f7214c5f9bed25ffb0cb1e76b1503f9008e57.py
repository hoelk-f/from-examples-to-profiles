def transform(x: str) -> str:
    parts = x.strip().split()
    return parts[-1] if parts else ""