def transform(x: str) -> str:
    parts = x.split(',', 1)
    return parts[1].lstrip() if len(parts) > 1 else x