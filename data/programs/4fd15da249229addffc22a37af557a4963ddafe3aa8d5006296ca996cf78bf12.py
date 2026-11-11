def transform(x: str) -> str:
    return x[x.rindex('(') + 1 : x.rindex(')')]