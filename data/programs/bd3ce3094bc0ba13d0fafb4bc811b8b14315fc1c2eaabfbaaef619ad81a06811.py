def transform(x: str) -> str:
    idx = x.rfind('/')
    if idx == -1:
        return ''
    return x[: idx + 1]