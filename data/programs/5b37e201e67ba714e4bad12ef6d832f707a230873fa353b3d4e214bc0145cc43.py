def transform(x: str) -> str:
    inner = x[x.index('<') + 1 : x.index('>')]
    return inner.rsplit('.', 1)[0]