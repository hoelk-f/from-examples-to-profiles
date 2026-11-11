def transform(x: str) -> str:
    """
    Extracts the word immediately following the first comma in the input string.
    """
    # Find the first comma
    idx = x.find(',')
    if idx == -1:
        return ""
    # Substring after the comma
    after = x[idx + 1 :].lstrip()
    # Return the first token before any whitespace
    return after.split()[0] if after else ""