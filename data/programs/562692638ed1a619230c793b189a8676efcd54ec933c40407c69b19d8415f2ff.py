def transform(x: str) -> str:
    tokens = x.split()
    result = []
    for token in tokens:
        if token.isdigit():
            break
        result.append(token)
    return " ".join(result)