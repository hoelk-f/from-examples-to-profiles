import re

def transform(x: str) -> str:
    numbers = re.findall(r'\d+', x)
    if not numbers:
        return ""
    return max(numbers, key=len)