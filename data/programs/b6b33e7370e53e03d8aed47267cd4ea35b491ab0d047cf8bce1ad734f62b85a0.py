def transform(x: str) -> str:
    """
    Extracts the content inside the last pair of parentheses in the string.
    Returns the trimmed substring, or an empty string if no such parentheses exist.
    """
    # Find the last opening parenthesis
    open_idx = x.rfind('(')
    close_idx = x.rfind(')')
    if open_idx == -1 or close_idx == -1 or close_idx <= open_idx:
        return ''
    return x[open_idx + 1:close_idx].strip()