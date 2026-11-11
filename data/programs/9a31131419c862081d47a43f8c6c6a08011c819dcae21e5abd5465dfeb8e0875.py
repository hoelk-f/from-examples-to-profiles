import re

def transform(x: str) -> str:
    return re.search(r'(\d+) Lips', x).group(1)
