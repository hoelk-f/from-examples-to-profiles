def transform(x: str) -> str:
    """
    Extract the number of inferences from a log line.
    The number appears before the literal substring " inferences".
    """
    # Split on the marker and take the part before it
    before = x.split(" inferences", 1)[0]
    # Strip any surrounding whitespace
    return before.strip()