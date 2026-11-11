def transform(x: str) -> str:
    idx = x.rfind("/")
    return x[:idx+1]
