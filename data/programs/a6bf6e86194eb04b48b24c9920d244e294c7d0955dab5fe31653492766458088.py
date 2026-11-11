def transform(x: str) -> str:
    # Remove leading numbering like "5. " if present
    if ". " in x:
        _, rest = x.split(". ", 1)
    else:
        rest = x
    # Remove trailing price part after the first comma
    if "," in rest:
        title, _ = rest.split(",", 1)
    else:
        title = rest
    return title.strip()