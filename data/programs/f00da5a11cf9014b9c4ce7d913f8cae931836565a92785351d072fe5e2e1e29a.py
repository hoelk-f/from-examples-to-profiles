def transform(x: str) -> str:
    if x.endswith('.'):
        return x[:-1]
    return x