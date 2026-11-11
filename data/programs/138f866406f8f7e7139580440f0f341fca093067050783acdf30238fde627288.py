def transform(x: str) -> str:
    idx = x.find(':')
    if idx == -1:
        return x.strip()
    return x[idx + 1 :].lstrip()