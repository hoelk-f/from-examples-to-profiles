def transform(x: str) -> str:
    parts = []
    for token in x.split():
        if token and token[0].isdigit():
            break
        parts.append(token)
    return " ".join(parts)