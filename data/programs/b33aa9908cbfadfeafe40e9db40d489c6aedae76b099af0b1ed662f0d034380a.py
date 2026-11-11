def transform(x: str) -> str:
    import re
    return re.sub(r'^\d+\s+', '', x).rsplit(' (', 1)[0]
