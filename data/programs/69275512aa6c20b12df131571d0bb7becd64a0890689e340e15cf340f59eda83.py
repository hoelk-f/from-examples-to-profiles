import re

def transform(x: str) -> str:
    """Remove XML/HTML tags from the input string."""
    return re.sub(r'<[^>]+>', '', x)