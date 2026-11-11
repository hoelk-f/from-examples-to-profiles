def transform(x: str) -> str:
    return x[:x.rfind('/') + 1]
