def transform(x: str) -> str:
    parts = x.split()
    name_parts = []
    for token in parts:
        if token and token[0].isdigit():
            break
        name_parts.append(token)
    return " ".join(name_parts)