def transform(x: str) -> str:
    import string
    words = x.split()
    if not words:
        return ""
    last = words[-1].strip(string.punctuation)
    return last