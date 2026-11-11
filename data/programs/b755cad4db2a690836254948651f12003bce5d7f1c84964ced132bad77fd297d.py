def transform(x: str) -> str:
    start = x.index('{')
    end = x.rindex('}')
    return x[start + 1 : end]
