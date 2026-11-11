import re

def transform(x: str) -> str:
    matches = re.findall(r'\b\d{5}\b', x)
    return matches[-1] if matches else ""