import re

def transform(x: str) -> str:
    matches = re.findall(r'@\S+', x)
    return matches[-1] if matches else ''