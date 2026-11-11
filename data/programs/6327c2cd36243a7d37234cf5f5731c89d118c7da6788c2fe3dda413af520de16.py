def transform(x: str) -> str:
    # Split off the leading numbered prefix (e.g., "01. ")
    parts = x.split('. ', 1)
    if len(parts) == 2:
        remainder = parts[1]
    else:
        remainder = x
    # Split before the hyphen separator and take the first segment
    first_segment = remainder.split(' - ', 1)[0]
    return first_segment.strip()