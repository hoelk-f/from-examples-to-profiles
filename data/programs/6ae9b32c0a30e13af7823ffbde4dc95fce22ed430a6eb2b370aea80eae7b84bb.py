def transform(x: str) -> str:
    """
    Extracts the first occurrence of a four‑digit year inside parentheses.
    If no such pattern is found, returns an empty string.
    """
    start = x.find('(')
    end = x.find(')', start + 1)
    if start != -1 and end != -1:
        candidate = x[start + 1:end]
        # Return the candidate if it looks like a year (4 digits)
        if candidate.isdigit() and len(candidate) == 4:
            return candidate
    return ""