import re

def transform(x: str) -> str:
    return re.search(r'About (\d[\d,]*)', x).group(1)
