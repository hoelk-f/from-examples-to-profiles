def transform(x: str) -> str:
    parts = x.split()
    if len(parts) >= 2:
        return f"{parts[0]} {parts[1]}"
    return x.strip()