def transform(x: str) -> str:
    """
    Extracts the month name from a string formatted like:
    "<day> <Month>,<year> (...)".
    """
    # Take the substring before the first comma
    before_comma = x.split(",", 1)[0]
    # The month is the last word in that segment
    return before_comma.split()[-1]