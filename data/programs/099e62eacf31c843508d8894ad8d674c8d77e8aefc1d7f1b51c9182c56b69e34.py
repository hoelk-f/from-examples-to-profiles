def transform(x: str) -> str:
    idx = x.find('@')
    if idx == -1:
        return ''
    return x[idx:].strip()