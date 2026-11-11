def transform(x: str) -> str:
    idx = x.find("//")
    return x[idx + 2 :] if idx != -1 else x