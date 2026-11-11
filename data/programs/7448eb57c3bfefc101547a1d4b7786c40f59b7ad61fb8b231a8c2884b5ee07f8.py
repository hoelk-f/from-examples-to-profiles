def transform(x: str) -> str:
    start = x.index('<country>') + len('<country>')
    end = x.index('</country>')
    return x[start:end]
