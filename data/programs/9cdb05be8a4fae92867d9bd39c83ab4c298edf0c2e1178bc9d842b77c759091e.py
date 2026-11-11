import re

def transform(x: str) -> str:
    result = re.sub(r'^\d+\.\s*', '', x)
    result = re.sub(r',\s*\$[\d.]+$', '', result)
    return result
