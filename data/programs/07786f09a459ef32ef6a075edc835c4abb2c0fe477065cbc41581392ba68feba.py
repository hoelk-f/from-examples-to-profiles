def transform(x: str) -> str:
    i = x.find('(')
    return x[:i].rstrip() if i != -1 else x.rstrip()