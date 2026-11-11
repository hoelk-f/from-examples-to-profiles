def transform(x: str) -> str:
    first = x.split(' ')[0]
    parts = first.split('-')
    return '-'.join(parts[1:])
