import re

def transform(x: str) -> str:
    return re.sub(r' \(\d+ years old\)$', '', x)
