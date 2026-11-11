import re

def transform(x: str) -> str:
    # Find a UK postcode (outward code + inward code)
    m = re.search(r'\b[A-Z]{1,2}\d{1,2}\s*\d[A-Z]{2}\b', x)
    if not m:
        return ""
    preceding = x[:m.start()]
    words = re.findall(r"[A-Za-z]+", preceding)
    return words[-1] if words else ""