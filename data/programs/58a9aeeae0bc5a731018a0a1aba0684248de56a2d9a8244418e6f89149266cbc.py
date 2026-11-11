def transform(x: str) -> str:
    # Split at the first dot to remove the leading number and dot
    parts = x.split(".", 1)
    if len(parts) < 2:
        return x.strip()
    after_dot = parts[1].lstrip()
    # Split at the first " - " (space dash space) to discard the trailing part
    middle = after_dot.split(" - ", 1)[0]
    return middle.strip()