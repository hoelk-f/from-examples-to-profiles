def transform(x: str) -> str:
    parts = x.split()
    name_parts = []
    for token in parts[1:]:
        if '-' in token and token.replace('-', '').isdigit():
            break
        name_parts.append(token)
    return ' '.join(name_parts)