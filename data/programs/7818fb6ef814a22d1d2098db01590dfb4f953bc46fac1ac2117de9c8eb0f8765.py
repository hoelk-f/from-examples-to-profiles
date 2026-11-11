def transform(x: str) -> str:
    for token in x.split():
        if ':' in token:
            return token
    return ""