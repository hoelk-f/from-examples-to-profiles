def transform(x: str) -> str:
    idx = x.find('-')
    return x[idx:] if idx != -1 else x