def transform(x: str) -> str:
    # Split off leading numbering like "01. "
    parts = x.split('. ', 1)
    if len(parts) == 2:
        x = parts[1]
    # Take the segment before the first " - "
    x = x.split(' - ', 1)[0]
    return x.strip()