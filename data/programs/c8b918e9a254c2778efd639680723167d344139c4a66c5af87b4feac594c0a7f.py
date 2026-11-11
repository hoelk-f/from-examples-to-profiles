def transform(x: str) -> str:
    parts = x.split('=', 1)
    if len(parts) == 2:
        return parts[1].strip()
    return x.strip()
