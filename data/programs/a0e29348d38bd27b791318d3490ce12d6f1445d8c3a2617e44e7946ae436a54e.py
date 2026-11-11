def transform(x: str) -> str:
    parts = x.split()
    if len(parts) < 2:
        return ""
    return parts[-2]