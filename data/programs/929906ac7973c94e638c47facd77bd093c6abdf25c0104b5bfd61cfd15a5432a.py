def transform(x: str) -> str:
    parts = x.split()
    if len(parts) > 2:
        return " ".join(parts[:-2])
    return x