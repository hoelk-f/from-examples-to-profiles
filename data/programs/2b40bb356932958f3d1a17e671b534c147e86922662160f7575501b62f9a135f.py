def transform(x: str) -> str:
    parts = x.split(';')
    if len(parts) < 2:
        return ''
    second = parts[1]
    first_sub = second.split(',')[0]
    return first_sub.strip()