def transform(x: str) -> str:
    parts = x.split()
    for i in range(len(parts) - 1):
        if parts[i + 1] == "following":
            return f"{parts[i]} following"
    return ""