import re

def transform(x: str) -> str:
    """Remove HTML-like tags from the input string."""
    return re.sub(r'<[^>]*>', '', x)