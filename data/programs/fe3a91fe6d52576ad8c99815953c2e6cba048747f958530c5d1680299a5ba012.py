import re

def transform(x: str) -> str:
    m = re.search(r'About (\d[\d,]*) results', x)
    return m.group(1)
