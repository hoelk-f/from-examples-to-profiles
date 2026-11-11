def transform(x: str) -> str:
    return x[4:] if x.startswith("www.") else x