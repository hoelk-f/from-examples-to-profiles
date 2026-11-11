import re

def transform(x: str) -> str:
    return re.search(r'About ([\d,]+) results', x).group(1)
