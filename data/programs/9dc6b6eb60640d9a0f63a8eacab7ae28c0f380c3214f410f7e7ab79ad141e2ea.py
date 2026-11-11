import re

def transform(x: str) -> str:
    words = re.findall(r"[A-Za-z0-9']+", x)
    return words[-1].lower() if words else ""