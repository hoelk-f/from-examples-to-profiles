def transform(x: str) -> str:
    return x[:-1] if x.endswith('.') else x