def transform(x: str) -> str:
    for token in x.split():
        if token.isdigit() and len(token) == 4:
            return token
    return ""