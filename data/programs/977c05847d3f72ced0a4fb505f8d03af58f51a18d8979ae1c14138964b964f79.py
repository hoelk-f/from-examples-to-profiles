def transform(x: str) -> str:
    idx = x.rfind('#')
    return x[idx:] if idx != -1 else x
