def transform(x: str) -> str:
    # Remove surrounding whitespace
    x = x.strip()
    if not x:
        return ""
    # Split into words
    words = x.split()
    # Take the last word
    last = words[-1]
    # Strip common punctuation from the ends
    return last.strip('.,!?:;\'"')