def transform(x: str) -> str:
    idx = x.rfind(" (")
    if idx != -1:
        x = x[:idx]
    idx = x.find(" ")
    if idx != -1:
        x = x[idx + 1:]
    return x
