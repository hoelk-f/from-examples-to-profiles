def transform(x: str) -> str:
    return x.split(". ", 1)[1].split(" - ")[0]
