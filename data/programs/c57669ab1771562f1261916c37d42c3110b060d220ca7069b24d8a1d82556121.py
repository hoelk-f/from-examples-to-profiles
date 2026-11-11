def transform(x: str) -> str:
    """
    Extracts the filename from a string that contains file metadata followed by the filename.
    The filename is assumed to be the last whitespace-separated token.
    """
    return x.strip().split()[-1]