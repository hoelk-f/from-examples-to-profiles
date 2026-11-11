def transform(x: str) -> str:
    parts = x.split('aka', 1)
    return parts[1].strip() if len(parts) > 1 else x.strip()
