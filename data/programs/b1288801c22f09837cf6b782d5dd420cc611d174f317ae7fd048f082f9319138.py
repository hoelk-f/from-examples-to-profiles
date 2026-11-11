def transform(x: str) -> str:
    for token in x.split():
        if ',' in token and any(c.isdigit() for c in token):
            return token
    return ""