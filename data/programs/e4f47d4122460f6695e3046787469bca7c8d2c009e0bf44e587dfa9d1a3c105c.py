import re

def transform(x: str) -> str:
    m = re.search(r'\((\d+)\s+years old\)', x)
    return m.group(1) if m else ""