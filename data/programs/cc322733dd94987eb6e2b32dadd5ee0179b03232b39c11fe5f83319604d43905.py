import re

def transform(x: str) -> str:
    m = re.search(r"x\d+", x)
    return m.group(0) if m else ""