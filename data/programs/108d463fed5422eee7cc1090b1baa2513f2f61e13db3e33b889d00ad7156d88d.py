def transform(x: str) -> str:
    phone = x.split(' ')[0]
    parts = phone.split('-')
    return '-'.join(parts[1:])
