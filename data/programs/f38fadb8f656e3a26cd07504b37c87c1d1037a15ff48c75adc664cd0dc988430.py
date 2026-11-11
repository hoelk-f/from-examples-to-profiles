def transform(x: str) -> str:
    parts = x.split()
    return f"{parts[-2]} {parts[-1]}" if len(parts) >= 2 else ""