def transform(x: str) -> str:
    parts = x.split()
    return " ".join(parts[1:]) if len(parts) > 1 else ""