def transform(x: str) -> str:
    for token in x.split():
        if ',' in token and any(ch.isdigit() for ch in token):
            return token
    return ""