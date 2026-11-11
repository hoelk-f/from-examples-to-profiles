def transform(x: str) -> str:
    import re
    match = re.search(r'\d+', x)
    return match.group(0) if match else ''