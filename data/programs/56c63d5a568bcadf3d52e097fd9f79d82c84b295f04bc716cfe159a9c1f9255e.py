def transform(x: str) -> str:
    inner = x[x.index('<')+1:x.index('>')]
    return inner.split(',')[-1]
