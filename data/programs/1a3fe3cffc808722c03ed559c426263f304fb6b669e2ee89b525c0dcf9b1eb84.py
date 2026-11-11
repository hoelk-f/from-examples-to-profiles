import re

def transform(x: str) -> str:
    return re.findall(r'\d+', x)[2]
