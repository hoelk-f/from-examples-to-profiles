def transform(x: str) -> str:
    return x.split("/")[-1] if "/" in x else x