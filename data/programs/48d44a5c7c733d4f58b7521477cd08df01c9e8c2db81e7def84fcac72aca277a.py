def transform(x: str) -> str:
    """
    Return the last word of the input string, stripped of surrounding punctuation.
    """
    # Remove leading/trailing whitespace
    stripped = x.strip()
    if not stripped:
        return ""
    # Split by whitespace and take the last token
    last_token = stripped.split()[-1]
    # Strip common punctuation from the ends of the word
    return last_token.strip('.,!?;:"\'()[]{}')