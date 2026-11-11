def transform(x: str) -> str:
    # Remove leading index and dot
    if ". " in x:
        _, rest = x.split(". ", 1)
    else:
        rest = x
    # Remove trailing price after the first comma
    title = rest.split(",", 1)[0].strip()
    return title