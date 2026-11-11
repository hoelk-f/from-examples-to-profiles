def transform(x: str) -> str:
    import string
    # Remove surrounding whitespace
    x = x.strip()
    if not x:
        return ""
    # Split on whitespace and take the last token
    last = x.split()[-1]
    # Strip surrounding punctuation
    return last.strip(string.punctuation)