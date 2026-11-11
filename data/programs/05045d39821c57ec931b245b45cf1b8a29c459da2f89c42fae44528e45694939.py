def transform(x: str) -> str:
    # Take the part before the first " - "
    left = x.split(" - ", 1)[0]
    # Remove leading numbering like "01. " or "010. "
    if ". " in left:
        return left.split(". ", 1)[1]
    # Fallback: strip leading digits, dot, and optional spaces
    import re
    m = re.search(r'^\d+\.\s*(.*)', left)
    return m.group(1) if m else left