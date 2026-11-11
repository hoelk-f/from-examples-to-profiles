def transform(x: str) -> str:
    idx = x.rfind('=')
    if idx == -1:
        return x
    return x[idx + 1 :].lstrip()