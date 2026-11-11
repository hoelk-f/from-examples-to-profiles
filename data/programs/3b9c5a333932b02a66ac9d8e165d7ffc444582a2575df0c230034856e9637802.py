import re

def transform(x: str) -> str:
    return re.search(r'(\d+\.\d+) CPU', x).group(1)
