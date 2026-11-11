import re

def transform(x: str) -> str:
    left = x.split(' - ', 1)[0]
    return re.sub(r'^\d+\.\s*', '', left)