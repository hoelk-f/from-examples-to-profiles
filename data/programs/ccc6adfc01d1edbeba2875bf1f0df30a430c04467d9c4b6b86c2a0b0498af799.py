def transform(x: str) -> str:
    import re
    numbers = re.findall(r'\d+', x)
    return numbers[-1] if numbers else ""