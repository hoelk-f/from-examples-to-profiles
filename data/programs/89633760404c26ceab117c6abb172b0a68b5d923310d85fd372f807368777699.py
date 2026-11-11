def transform(x: str) -> str:
    i = x.find(' ')
    return x[i + 1:] if i != -1 else ''