import re

def transform(x: str) -> str:
    # Pattern for UK postcode (simplified)
    postcode_pattern = re.compile(r'\b[A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2}\b')
    m = postcode_pattern.search(x)
    if m:
        before = x[:m.start()].rstrip()
    else:
        before = x.rstrip()
    # Take the part after the last comma, if any
    if ',' in before:
        city_part = before.split(',')[-1].strip()
    else:
        # Fallback: take the last word before the postcode
        city_part = before.split()[-1].strip()
    return city_part