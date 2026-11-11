def transform(x: str) -> str:
    i = x.find('-')
    return x[i:] if i != -1 else ''