def transform(x: str) -> str:
    """
    Extracts the portion of the string that appears after the first ". "
    and before the first " -". Leading and trailing whitespace are removed.
    """
    # Get the part after the first ". "
    parts = x.split('. ', 1)
    after_dot = parts[1] if len(parts) > 1 else parts[0]

    # Get the part before the first " -"
    before_dash = after_dot.split(' -', 1)[0]

    return before_dash.strip()