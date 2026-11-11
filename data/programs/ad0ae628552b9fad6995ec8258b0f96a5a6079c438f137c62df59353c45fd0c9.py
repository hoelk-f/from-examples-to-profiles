def transform(x: str) -> str:
    idx = x.find('(')
    if idx != -1:
        return x[:idx].strip()
    return x.strip()