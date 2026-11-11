import re

def transform(x: str) -> str:
    # Find all word-like tokens (letters and apostrophes)
    words = re.findall(r"[A-Za-z']+", x)
    return words[-1] if words else ""