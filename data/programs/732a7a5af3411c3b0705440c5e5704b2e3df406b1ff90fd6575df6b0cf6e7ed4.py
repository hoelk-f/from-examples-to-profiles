def transform(x: str) -> str:
    parts = x.split(" - ", 1)
    return parts[0] if parts else x