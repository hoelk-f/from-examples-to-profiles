def transform(x: str) -> str:
    """
    Return the portion of the string that follows the first occurrence of 'aka '.
    If 'aka ' is not present, return the original string stripped of surrounding whitespace.
    """
    parts = x.split("aka ", 1)
    return parts[1].strip() if len(parts) == 2 else x.strip()