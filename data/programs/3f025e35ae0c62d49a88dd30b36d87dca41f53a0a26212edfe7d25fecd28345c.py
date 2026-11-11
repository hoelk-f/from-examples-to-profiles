def transform(x: str) -> str:
    start = x.index('(') + 1
    end = x.index(';', start)
    return x[start:end]
