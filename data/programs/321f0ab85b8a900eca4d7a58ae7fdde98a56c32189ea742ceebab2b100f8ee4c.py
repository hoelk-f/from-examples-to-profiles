def transform(x: str) -> str:
    tokens = x.split()
    name_parts = []
    for token in tokens:
        if token and token[0].isdigit():
            break
        name_parts.append(token)
    return " ".join(name_parts)