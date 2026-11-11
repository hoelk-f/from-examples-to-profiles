def transform(x: str) -> str:
    for token in x.split():
        if token.isdigit() and '0' in token:
            return token
    return ""