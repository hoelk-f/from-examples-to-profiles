import re

def transform(x: str) -> str:
    """
    Remove a trailing parenthesized expression (e.g., a year) and any surrounding whitespace.
    """
    return re.sub(r'\s*\([^)]*\)\s*$', '', x)