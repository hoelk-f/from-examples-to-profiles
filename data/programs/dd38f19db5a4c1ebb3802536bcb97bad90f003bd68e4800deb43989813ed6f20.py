import re

def transform(x: str) -> str:
    """
    Extracts the year (a sequence of digits) that appears inside the last pair of parentheses.
    """
    match = re.search(r'\((\d{4})\)\s*$', x)
    if match:
        return match.group(1)
    # Fallback: find any 4‑digit number in parentheses
    match = re.search(r'\((\d{4})\)', x)
    return match.group(1) if match else ""