import re

def transform(x: str) -> str:
    return re.search(r'\d+ \w+ \d{1,2}:\d{2}', x).group(0)
