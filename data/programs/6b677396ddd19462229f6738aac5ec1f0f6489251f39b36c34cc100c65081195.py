import re

def transform(x: str) -> str:
    m = re.search(r'\d{1,2}:\d{2}', x)
    return m.group(0) if m else ''
