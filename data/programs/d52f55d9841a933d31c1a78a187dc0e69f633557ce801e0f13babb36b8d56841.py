import re

def transform(x: str) -> str:
    m = re.search(r'\d{4}', x)
    return x[m.start():] if m else x
