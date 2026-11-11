def transform(x: str) -> str:
    start = x.find(' ') + 1
    end = x.find(',', start)
    return x[start:end]