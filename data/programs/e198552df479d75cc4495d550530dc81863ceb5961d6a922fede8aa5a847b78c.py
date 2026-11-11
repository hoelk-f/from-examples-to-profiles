def transform(x: str) -> str:
    # Remove leading numbering like "01. "
    if ". " in x:
        _, after_dot = x.split(". ", 1)
    else:
        after_dot = x
    # Take text before the first " -"
    if " -" in after_dot:
        result = after_dot.split(" -", 1)[0]
    else:
        result = after_dot
    return result.strip()