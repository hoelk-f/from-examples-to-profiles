import re

def transform(x: str) -> str:
    # Take the part before the first " - "
    part = x.split(" - ", 1)[0]
    # Remove leading numbering like "01. " or "1.   "
    part = re.sub(r'^\d+\.\s*', '', part)
    return part.strip()