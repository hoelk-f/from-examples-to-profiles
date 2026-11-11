def transform(x: str) -> str:
    parts = x.split()
    if len(parts) >= 4:
        return " ".join(parts[1:4])
    return ""