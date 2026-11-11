def transform(x: str) -> str:
    start = x.index('(') + 1
    end = x.index(')')
    return x[start:end]