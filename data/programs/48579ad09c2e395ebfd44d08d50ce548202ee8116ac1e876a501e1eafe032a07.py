import re

def transform(x: str) -> str:
    parts = x.split(',', 1)
    if len(parts) < 2:
        return x.strip()
    number_part = parts[0].strip()
    rest = parts[1]
    m = re.search(r'\d', rest)
    if not m:
        street = rest.strip()
    else:
        street = rest[:m.start()].strip()
    return f"{number_part}, {street}"