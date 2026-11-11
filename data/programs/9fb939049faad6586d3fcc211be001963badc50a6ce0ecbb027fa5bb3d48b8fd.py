import re

def transform(x: str) -> str:
    m = re.search(r'\d{2,}\s+[A-Z]', x)
    if m:
        return x[:m.start()].strip()
    return x
