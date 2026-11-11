def transform(x: str) -> str:
    i = x.rfind('.')
    return x[i:] if i != -1 else ''