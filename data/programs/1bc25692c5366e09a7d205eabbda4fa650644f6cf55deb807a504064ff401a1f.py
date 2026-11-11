def transform(x: str) -> str:
    import re
    matches = re.findall(r"\d+", x)
    return matches[-1] if matches else ""