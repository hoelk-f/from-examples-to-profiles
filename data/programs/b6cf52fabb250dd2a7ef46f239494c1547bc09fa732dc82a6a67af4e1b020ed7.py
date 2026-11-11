def transform(x: str) -> str:
    parts = x.strip().split()
    if len(parts) >= 2:
        return f"{parts[-2]} {parts[-1]}"
    return ""