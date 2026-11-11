def transform(x: str) -> str:
    after_comma = x.split(", ", 1)[1]
    return after_comma.split(" 4 ")[0]
