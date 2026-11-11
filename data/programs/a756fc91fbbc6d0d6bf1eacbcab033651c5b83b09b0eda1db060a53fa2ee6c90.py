def transform(x: str) -> str:
    return ''.join(c for c in x if c.isdigit())[-3:]
