import re

def transform(x: str) -> str:
    """
    Extracts the first contiguous sequence of digits from the input string.
    """
    match = re.search(r'\d+', x)
    return match.group(0) if match else ""