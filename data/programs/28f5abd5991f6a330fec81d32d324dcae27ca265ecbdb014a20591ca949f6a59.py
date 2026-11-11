import re

def transform(x: str) -> str:
    return re.search(r'\d{2}:\d{2}', x).group()
