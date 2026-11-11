import re

def transform(x: str) -> str:
    return re.search(r'\d{1,3}(?:,\d{3})+', x).group()
