def transform(x: str) -> str:
    import re
    matches = re.findall(r"\d{5}", x)
    return matches[-1] if matches else ""