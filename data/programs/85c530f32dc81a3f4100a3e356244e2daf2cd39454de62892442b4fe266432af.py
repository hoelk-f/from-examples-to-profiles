def transform(x: str) -> str:
    i = x.rfind('\\')
    return x[:i + 1] if i != -1 else ''