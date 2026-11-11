import re

def transform(x: str) -> str:
    """Extract numeric characters and commas from the input string."""
    return re.sub(r'[^0-9,]', '', x)