import re

def transform(x: str) -> str:
    return re.search(r'\((\d+)\s+years old\)', x).group(1)
