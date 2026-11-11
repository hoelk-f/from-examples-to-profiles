def transform(x: str) -> str:
    """
    Extracts the substring that appears after the first occurrence of a period
    followed by a space, and before the first occurrence of a space‑dash
    sequence (" -").
    """
    # Find the part after the first ". "
    try:
        _, after_dot = x.split('. ', 1)
    except ValueError:
        return ''
    # Find the part before " -"
    before_dash = after_dot.split(' -', 1)[0]
    return before_dash.strip()