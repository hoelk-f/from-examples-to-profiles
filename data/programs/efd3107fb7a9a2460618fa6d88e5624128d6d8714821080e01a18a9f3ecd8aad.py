import re

def transform(x: str) -> str:
    m = re.search(r'\b\d{4}\b', x)
    return x[m.start():]
