def transform(x: str) -> str:
    # Split off the leading numbering and period
    parts = x.split('. ', 1)
    if len(parts) < 2:
        return x
    # Take the segment after the period
    after_dot = parts[1]
    # Split on the delimiter before the second part
    first_segment = after_dot.split(' -', 1)[0]
    return first_segment.strip()