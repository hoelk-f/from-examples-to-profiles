import re

def transform(x: str) -> str:
    return re.search(r'\((.+?)\)', x).group(1)
