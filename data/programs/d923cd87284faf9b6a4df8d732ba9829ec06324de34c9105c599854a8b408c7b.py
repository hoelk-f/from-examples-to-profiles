def transform(x: str) -> str:
    parts = x.split()
    return f"{parts[1]} {parts[2]}" if len(parts) >= 3 else ""