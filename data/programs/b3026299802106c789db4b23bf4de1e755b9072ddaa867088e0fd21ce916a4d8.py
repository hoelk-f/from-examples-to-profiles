def transform(x: str) -> str:
    idx = x.find('(')
    if idx != -1:
        x = x[:idx]
    return x.rstrip()