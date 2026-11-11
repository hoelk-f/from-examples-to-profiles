def transform(x: str) -> str:
    tokens = x.split(' ')
    return ' '.join(tokens[:-2])
