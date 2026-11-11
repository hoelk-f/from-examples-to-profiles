import re

def transform(x: str) -> str:
    return re.search(r'([A-Z]{2}), Italy', x).group(1)
