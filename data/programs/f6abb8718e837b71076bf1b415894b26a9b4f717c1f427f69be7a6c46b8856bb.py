def transform(x: str) -> str:
    try:
        time_part = x.split()[-1]
        parts = time_part.split(":")
        if len(parts) >= 2:
            return parts[1]
    except Exception:
        pass
    return ""