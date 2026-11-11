def transform(x: str) -> str:
    pos = x.rfind("\\")
    return x[:pos + 1] if pos != -1 else ""