def transform(x: str) -> str:
    last_tag = ""
    for token in x.split():
        if token.startswith("#"):
            last_tag = token
    return last_tag