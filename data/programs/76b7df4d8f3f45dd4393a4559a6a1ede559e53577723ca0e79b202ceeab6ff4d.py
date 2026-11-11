import re

def transform(x: str) -> str:
    numbers = re.findall(r"\d+", x)
    return numbers[-1] if numbers else ""