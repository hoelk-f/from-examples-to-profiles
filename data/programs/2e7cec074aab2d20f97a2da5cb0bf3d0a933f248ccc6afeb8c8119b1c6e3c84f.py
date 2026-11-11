def transform(x: str) -> str:
    return x[x.index("(") + 1 : x.rindex(")")]
