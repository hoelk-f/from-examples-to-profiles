def transform(x: str) -> str:
    start = x.index('<price>') + len('<price>')
    end = x.index('</price>')
    return x[start:end]
