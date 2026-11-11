def transform(x: str) -> str:
    parts = [p.strip() for p in x.split(",")]
    return ", ".join(parts[-2:])
