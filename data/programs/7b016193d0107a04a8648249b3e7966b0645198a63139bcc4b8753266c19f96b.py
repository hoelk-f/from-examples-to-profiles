def transform(x: str) -> str:
    parts = x.split()
    for i, token in enumerate(parts):
        if token == "following" and i > 0:
            return f"{parts[i-1]} following"
    return ""