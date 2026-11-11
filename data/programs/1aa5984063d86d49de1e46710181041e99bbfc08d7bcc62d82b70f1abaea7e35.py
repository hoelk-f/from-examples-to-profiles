import re

def transform(x: str) -> str:
    m = re.search(r'\b\d{2}:\d{2}\b', x)
    return m.group(0) if m else ''