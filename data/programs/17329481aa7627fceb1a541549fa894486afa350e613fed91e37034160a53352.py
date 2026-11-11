def transform(x: str) -> str:
    after_dot = x.split(". ", 1)[1]
    return after_dot.split(" - ")[0]
