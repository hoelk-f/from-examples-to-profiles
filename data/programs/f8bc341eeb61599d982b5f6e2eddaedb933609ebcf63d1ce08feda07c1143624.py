def transform(x: str) -> str:
    for token in x.split():
        if "," in token and token.replace(",", "").isdigit():
            return token
    return ""