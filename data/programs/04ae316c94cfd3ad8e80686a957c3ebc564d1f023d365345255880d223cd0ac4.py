def transform(x: str) -> str:
    idx = x.rfind('.')
    return x[idx + 1 :] if idx != -1 else ""