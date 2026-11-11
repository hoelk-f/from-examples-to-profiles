import re

def transform(x: str) -> str:
    """
    Extracts the numeric year (or any digits) enclosed in the last pair of parentheses.
    If no such pattern is found, returns an empty string.
    """
    # Find all occurrences of '(' ... ')' and take the last one
    matches = re.findall(r'\(([^)]*)\)', x)
    if not matches:
        return ""
    # Take the last captured content
    content = matches[-1]
    # Extract digits from the content
    digits = re.search(r'\d+', content)
    return digits.group(0) if digits else ""