def transform(x: str) -> str:
    last_open = x.rfind('(')
    last_close = x.rfind(')')
    return x[last_open + 1:last_close]
