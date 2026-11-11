def transform(x: str) -> str:
    tokens = x.split()
    for token in tokens:
        if token.isdigit() and '0' in token:
            return token
    return ""