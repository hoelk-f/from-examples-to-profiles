def transform(x: str) -> str:
    import re
    matches = re.findall(r'\((\d{4})\)', x)
    return matches[-1] if matches else ""