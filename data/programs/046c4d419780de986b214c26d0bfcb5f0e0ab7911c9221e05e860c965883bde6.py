def transform(x: str) -> str:
    parts = x.split()
    if len(parts) >= 3:
        return f"{parts[1]} {parts[2]}"
    return ""