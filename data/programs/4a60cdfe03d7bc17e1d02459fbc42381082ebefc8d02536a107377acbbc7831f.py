import re

def transform(x: str) -> str:
    return re.search(r'inferences,\s*([\d.]+)\s+CPU', x).group(1)
