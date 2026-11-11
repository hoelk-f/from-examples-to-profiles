def transform(x: str) -> str:
    idx = x.find(" inferences")
    if idx != -1:
        return x[:idx]
    return x