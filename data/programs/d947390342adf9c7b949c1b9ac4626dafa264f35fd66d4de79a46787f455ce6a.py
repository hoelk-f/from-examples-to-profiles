def transform(x: str) -> str:
    i = x.find('X')
    return x[:i] if i != -1 else x