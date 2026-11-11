def transform(x: str) -> str:
    for token in x.split():
        if not token.isdigit():
            return token
    return ""