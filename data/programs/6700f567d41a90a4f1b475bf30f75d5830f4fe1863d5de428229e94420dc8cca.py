def transform(x: str) -> str:
    for token in x.split():
        if token.isdigit() and len(token) == 3:
            return token
    return ""