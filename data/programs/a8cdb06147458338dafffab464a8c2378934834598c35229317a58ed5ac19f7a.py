def transform(x: str) -> str:
    idx = x.find('=')
    if idx != -1:
        x = x[idx + 1 :]
    return x.lstrip()