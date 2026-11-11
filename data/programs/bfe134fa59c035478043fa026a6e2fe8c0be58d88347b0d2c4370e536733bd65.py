def transform(x: str) -> str:
    prefix = "model= "
    if x.startswith(prefix):
        return x[len(prefix):]
    return x
