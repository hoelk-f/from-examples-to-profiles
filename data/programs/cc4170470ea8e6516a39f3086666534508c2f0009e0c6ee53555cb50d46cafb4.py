def transform(x: str) -> str:
    # Remove leading numbering like "01. "
    if ". " in x:
        x = x.split(". ", 1)[1]
    # Keep text before the delimiter " - "
    if " - " in x:
        x = x.split(" - ", 1)[0]
    return x