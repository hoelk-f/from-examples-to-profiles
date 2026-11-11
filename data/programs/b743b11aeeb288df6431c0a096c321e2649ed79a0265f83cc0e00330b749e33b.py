import re

def transform(x: str) -> str:
    m = re.search(r'(\d{3})-(\d{3})-(\d{3})', x)
    return m.group(2) if m else ""