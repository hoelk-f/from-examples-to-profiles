import re

def transform(x: str) -> str:
    result = re.sub(r'^\d+\.\s+', '', x)
    return result.split(' - ')[0]
