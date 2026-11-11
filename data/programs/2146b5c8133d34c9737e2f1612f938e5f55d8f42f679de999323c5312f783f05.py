def transform(x: str) -> str:
    """
    Extracts the substring after the dash in the portion of the input string
    that follows the last '/' character.
    """
    # Get the segment after the last '/'
    after_slash = x.rsplit('/', 1)[-1]
    # Return the part after the last '-'
    return after_slash.rsplit('-', 1)[-1]