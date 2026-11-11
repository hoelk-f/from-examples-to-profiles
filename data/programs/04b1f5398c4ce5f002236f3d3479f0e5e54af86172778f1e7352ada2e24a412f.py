def transform(x: str) -> str:
    start = x.rfind('(') + 1
    end = x.rfind(')')
    return x[start:end]
