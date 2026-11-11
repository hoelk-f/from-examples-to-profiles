def transform(x: str) -> str:
    parts = [p.strip() for p in x.split(",")]
    return parts[3] if len(parts) > 3 else ""