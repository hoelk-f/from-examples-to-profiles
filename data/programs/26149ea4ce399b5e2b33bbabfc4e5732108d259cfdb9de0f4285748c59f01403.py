import re

def transform(x: str) -> str:
    return re.search(r'\((\d{3})\)', x).group(1)
