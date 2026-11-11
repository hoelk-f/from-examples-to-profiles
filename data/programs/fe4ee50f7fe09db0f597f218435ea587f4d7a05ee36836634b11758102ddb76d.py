import re

def transform(x: str) -> str:
    return re.findall(r'\d{5}', x)[-1]
