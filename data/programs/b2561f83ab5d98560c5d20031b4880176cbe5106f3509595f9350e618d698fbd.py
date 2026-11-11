import re

def transform(x: str) -> str:
    match = re.search(r'\d{1,3}(,\d{3})+', x)
    return match.group()
