def transform(x: str) -> str:
    tokens = x.split()
    for i, token in enumerate(tokens):
        if ',' in token:
            return ' '.join(tokens[:i])
    return x
