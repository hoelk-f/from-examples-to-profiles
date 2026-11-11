import re

def transform(x: str) -> str:
    m = re.search(r'^\d+\. (\S+)', x)
    return m.group(1) if m else ""