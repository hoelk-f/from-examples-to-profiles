import re

def transform(x: str) -> str:
    return re.match(r'\d+\s+(.*?)\s+\(\w+\)', x).group(1)
