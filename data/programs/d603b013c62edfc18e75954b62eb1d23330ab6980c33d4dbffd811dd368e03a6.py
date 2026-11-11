def transform(x: str) -> str:
    # Extract the segment after the first hyphen
    try:
        after_hyphen = x.split("-", 1)[1]
    except IndexError:
        return ""
    # Take the portion before the first comma
    before_comma = after_hyphen.split(",", 1)[0]
    # The province code is the last whitespace-separated token
    tokens = before_comma.strip().split()
    return tokens[-1] if tokens else ""