def transform(x: str) -> str:
    start = x.index("(") + 1
    end = x.rindex(")")
    return x[start:end]
