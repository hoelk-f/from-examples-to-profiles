import re

def transform(x: str) -> str:
    m = re.search(r'[\d.]+g', x)
    return m.group(0)
