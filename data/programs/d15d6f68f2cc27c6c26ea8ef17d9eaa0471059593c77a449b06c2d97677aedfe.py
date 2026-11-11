def transform(x: str) -> str:
    for token in x.split():
        if token.isdigit() and token.endswith('0'):
            return token
    return ""