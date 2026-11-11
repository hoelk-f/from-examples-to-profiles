def transform(x: str) -> str:
    if x.startswith("BA "):
        return x[3:]
    return x
