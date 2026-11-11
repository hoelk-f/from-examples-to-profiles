def transform(x: str) -> str:
    parts = x.split('=', 1)
    return parts[1].strip() if len(parts) == 2 else x.strip()