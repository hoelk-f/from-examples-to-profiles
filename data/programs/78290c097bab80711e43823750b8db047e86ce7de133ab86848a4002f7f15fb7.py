import re

def transform(x: str) -> str:
    m = re.search(r"<price>(.*?)</price>", x, re.DOTALL)
    return m.group(1) if m else ""