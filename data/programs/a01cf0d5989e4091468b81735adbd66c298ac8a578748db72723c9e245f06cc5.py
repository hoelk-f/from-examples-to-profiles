def transform(x: str) -> str:
    idx = x.find('#')
    return x[idx:]