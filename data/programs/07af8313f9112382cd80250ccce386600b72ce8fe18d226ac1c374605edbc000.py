def transform(x: str) -> str:
    if x.startswith("www."):
        return x[4:]
    return x
