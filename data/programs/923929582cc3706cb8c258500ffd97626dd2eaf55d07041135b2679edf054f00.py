def transform(x: str) -> str:
    import re
    m = re.search(r'\b([A-Z]{2})\s*\d{5}\b', x)
    return m.group(1) if m else ""