import re

def transform(x: str) -> str:
    return re.search(r'(\d+) years old', x).group(1)
