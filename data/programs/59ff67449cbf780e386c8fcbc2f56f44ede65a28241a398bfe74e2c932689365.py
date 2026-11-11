def transform(x: str) -> str:
    parts = [part.strip() for part in x.split(",")]
    return parts[-1] if parts else ""