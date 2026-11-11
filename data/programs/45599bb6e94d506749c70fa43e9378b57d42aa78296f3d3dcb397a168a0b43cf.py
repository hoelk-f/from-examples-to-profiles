def transform(x: str) -> str:
    tokens = x.split()
    for i, token in enumerate(tokens):
        if token.isdigit():
            if i:
                return tokens[i - 1]
    return ""