def transform(x: str) -> str:
    import re
    # Split on actual newline characters or the literal sequence "/n"
    parts = re.split(r'\n|/n', x)
    # Filter out empty strings resulting from consecutive separators
    non_empty = [p for p in parts if p != ""]
    # Return the last non‑empty part, stripped of surrounding whitespace
    return non_empty[-1].strip() if non_empty else ""