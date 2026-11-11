import re

def transform(x: str) -> str:
    m = re.search(r'\d+(?:st|nd|rd|th)\s+([A-Z][a-z]+)', x)
    return m.group(1) if m else ""