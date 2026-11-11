def transform(x: str) -> str:
    """
    Extracts the model name from a vehicle description string.
    Assumes the model is the last whitespace-separated token.
    """
    return x.split()[-1] if x else ""