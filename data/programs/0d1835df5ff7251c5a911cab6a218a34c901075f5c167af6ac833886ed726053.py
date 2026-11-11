import re

def transform(x: str) -> str:
    x = re.sub(r'^\d+\s+', '', x)
    x = re.sub(r'\s*\([^)]*\)$', '', x)
    return x
