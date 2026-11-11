import re

def transform(x: str) -> str:
    # UK postcode pattern (simplified)
    postcode_pattern = re.compile(r"[A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2}", re.IGNORECASE)
    m = postcode_pattern.search(x)
    if m:
        prefix = x[:m.start()]
    else:
        prefix = x
    parts = prefix.split(',')
    # Take the last non‑empty part after stripping whitespace
    for part in reversed(parts):
        city = part.strip()
        if city:
            return city
    return ""