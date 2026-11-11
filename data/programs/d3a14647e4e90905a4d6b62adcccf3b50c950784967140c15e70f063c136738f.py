import re

def transform(x: str) -> str:
    m = re.search(r'\b([A-Z]{2})\s+\d{5}\b', x)
    if m:
        return m.group(1)
    parts = x.split(',')
    if len(parts) >= 2:
        state_zip = parts[-1].strip()
        tokens = state_zip.split()
        if tokens:
            return tokens[0]
    return ""