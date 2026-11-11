def transform(x: str) -> str:
    return x.split("(longitude)")[0].split(", ")[1]