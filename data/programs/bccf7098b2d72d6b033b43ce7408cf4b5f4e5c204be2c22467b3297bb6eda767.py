import re

def transform(x: str) -> str:
    m = re.search(r'\b[A-Za-z]{1,2}\d[A-Za-z]?\s\d[A-Za-z]{2}\b', x)
    return m.group(0).upper() if m else x
