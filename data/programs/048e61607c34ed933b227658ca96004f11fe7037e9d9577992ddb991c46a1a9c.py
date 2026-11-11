def transform(x: str) -> str:
    import re
    match = re.search(r'\b\d{2}/\d{2}\b', x)
    return match.group(0) if match else ""