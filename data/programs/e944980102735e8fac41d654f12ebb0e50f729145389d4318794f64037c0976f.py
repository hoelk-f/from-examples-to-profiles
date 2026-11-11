def transform(x: str) -> str:
    import re
    matches = re.findall(r'\b\d{4}\b', x)
    return matches[-1] if matches else ''