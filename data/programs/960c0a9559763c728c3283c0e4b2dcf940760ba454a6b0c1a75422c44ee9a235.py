def transform(x: str) -> str:
    digits = [c for c in x if c.isdigit()]
    return ''.join(digits[-3:])
