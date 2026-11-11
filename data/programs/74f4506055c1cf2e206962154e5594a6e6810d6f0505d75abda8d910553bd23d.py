import re

def transform(x: str) -> str:
    """
    Extracts the numeric part (digits and commas) from a string that may contain
    HTML tags and a pound sign entity.
    """
    match = re.search(r'[\d,]+', x)
    return match.group(0) if match else ""