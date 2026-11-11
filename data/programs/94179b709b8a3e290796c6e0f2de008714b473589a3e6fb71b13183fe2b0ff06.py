def transform(x: str) -> str:
    # Extract the part before the first '(' and strip whitespace
    return x.split('(')[0].strip()