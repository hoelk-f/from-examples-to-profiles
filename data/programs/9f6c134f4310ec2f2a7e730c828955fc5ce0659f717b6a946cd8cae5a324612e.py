def transform(x: str) -> str:
    first_part = x.split(' ')[0]
    parts = first_part.split('-')
    return '-'.join(parts[1:])
