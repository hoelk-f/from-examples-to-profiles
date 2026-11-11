def transform(x: str) -> str:
    """
    Extract the leading numeric token (typically a year) from the input string.
    """
    # Split the string by whitespace and return the first token that consists of digits.
    for token in x.split():
        if token.isdigit():
            return token
    # Fallback: return empty string if no numeric token is found.
    return ""