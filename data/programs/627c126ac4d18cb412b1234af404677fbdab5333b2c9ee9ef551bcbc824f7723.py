import re

def transform(x: str) -> str:
    m = re.search(r'CPU in ([0-9]+\.[0-9]+)', x)
    return m.group(1) if m else ''