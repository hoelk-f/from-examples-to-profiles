import re

def transform(x: str) -> str:
    return re.search(r'[\d.]+g', x).group()
