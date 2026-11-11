def transform(x: str) -> str:
    import re
    match = re.search(r'\((\d{4})\)', x)
    return match.group(1) if match else ""