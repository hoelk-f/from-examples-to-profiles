import re

def transform(x: str) -> str:
    """
    Remove a trailing space followed by a parenthesized integer from the end of the string.
    Example: "Team Name (5)" -> "Team Name"
    """
    return re.sub(r'\s*\(\d+\)\s*$', '', x)