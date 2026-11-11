def transform(x: str) -> str:
    start = x.index('(')
    end = x.index(')')
    return x[start+1:end]
