def transform(x: str) -> str:
    parts = x.rsplit(".", 1)
    return parts[1] if len(parts) == 2 else ""