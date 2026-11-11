def transform(x: str) -> str:
    return x.rsplit('.', 1)[-1]