def transform(x: str) -> str:
    if x.startswith('$'):
        return x[1:]
    return x