def transform(x: str) -> str:
    # Split on whitespace, take the last token
    token = x.strip().split()[-1]
    # Strip surrounding punctuation characters
    return token.strip('.,;:!?"\'()[]{}')