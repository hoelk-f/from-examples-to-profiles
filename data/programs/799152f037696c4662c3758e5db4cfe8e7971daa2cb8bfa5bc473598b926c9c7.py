import re

def transform(x: str) -> str:
    m = re.search(r'(\d+)\s+following', x)
    return f"{m.group(1)} following" if m else ""