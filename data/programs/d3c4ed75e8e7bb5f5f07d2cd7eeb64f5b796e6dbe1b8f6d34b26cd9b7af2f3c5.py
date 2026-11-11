import re

def transform(x: str) -> str:
    matches = re.findall(r"\d{5}", x)
    return matches[-1] if matches else ""