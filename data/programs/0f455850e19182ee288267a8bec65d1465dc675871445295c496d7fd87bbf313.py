def transform(x: str) -> str:
    inner = x.split('<')[1].rstrip('>')
    return inner.split(',')[-1]
