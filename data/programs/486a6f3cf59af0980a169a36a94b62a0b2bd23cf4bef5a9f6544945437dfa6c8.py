def transform(x: str) -> str:
    return x[1:] if x.startswith("$") else x