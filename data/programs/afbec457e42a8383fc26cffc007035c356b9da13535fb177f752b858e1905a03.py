def transform(x: str) -> str:
    x = x.split(". ", 1)[1]
    x = x.rsplit(", $", 1)[0]
    return x
