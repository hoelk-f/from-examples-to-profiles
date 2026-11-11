def transform(x: str) -> str:
    parts = x.split()
    if len(parts) < 2:
        return ""
    segment = parts[1]
    return segment.split("-")[0]