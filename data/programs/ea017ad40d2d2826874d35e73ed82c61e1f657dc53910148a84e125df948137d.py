import re

def transform(x: str) -> str:
    return re.search(r'\((\d{4})\)', x).group(1)
