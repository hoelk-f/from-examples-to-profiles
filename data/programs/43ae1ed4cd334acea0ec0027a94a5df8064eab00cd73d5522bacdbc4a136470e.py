def transform(x: str) -> str:
    parts = x.split(';')
    if len(parts) < 2:
        return ''
    middle = parts[1]
    first_token = middle.split(',')[0]
    return first_token.strip()