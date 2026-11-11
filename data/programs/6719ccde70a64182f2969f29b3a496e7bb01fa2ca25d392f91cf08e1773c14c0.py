import re

def transform(x: str) -> str:
    return re.search(r'\b\d{4}\b', x).group()
