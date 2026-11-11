def transform(x: str) -> str:
    parts = x.strip().split()
    if not parts:
        return ""
    time_part = parts[-1]
    segments = time_part.split(":")
    return segments[-1] if segments else ""