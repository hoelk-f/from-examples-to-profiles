def transform(x: str) -> str:
    """
    Extracts the version string that follows the last hyphen in the portion of the input
    after the final '/' character.
    """
    # Get the segment after the last slash
    after_slash = x.rsplit('/', 1)[-1]
    # Return the part after the last hyphen
    return after_slash.rsplit('-', 1)[-1]