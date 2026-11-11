import re

def transform(x: str) -> str:
    match = re.search(r'\b([A-Z]{2})\b(?=,)', x)
    return match.group(1) if match else ""