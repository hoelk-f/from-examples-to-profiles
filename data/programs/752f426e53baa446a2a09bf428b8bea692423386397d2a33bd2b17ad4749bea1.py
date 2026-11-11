def transform(x: str) -> str:
    """
    Extract the Twitter handle (without the leading '@') from the input string.
    The handle is assumed to start with '@' and continue until the next whitespace.
    """
    if '@' not in x:
        return ''
    after_at = x.split('@', 1)[1]
    handle = after_at.split(None, 1)[0]  # split on any whitespace
    return handle