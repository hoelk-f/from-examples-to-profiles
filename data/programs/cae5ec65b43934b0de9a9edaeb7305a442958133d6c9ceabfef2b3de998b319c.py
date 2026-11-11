import re

def transform(x: str) -> str:
    m = re.search(r'\d+(?:am|pm)-\d+(?:am|pm)', x)
    return m.group(0) if m else ""