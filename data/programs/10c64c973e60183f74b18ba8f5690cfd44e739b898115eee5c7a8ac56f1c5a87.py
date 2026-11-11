def transform(x: str) -> str:
    """
    Extract the three-digit group that appears after the first space
    and before the first hyphen in the input string.
    """
    # Split at the first space
    parts = x.split(' ', 1)
    if len(parts) < 2:
        return ''
    after_space = parts[1]
    # Take the segment before the first hyphen
    segment = after_space.split('-', 1)[0]
    # Return the first three characters (the expected group)
    return segment[:3]