def transform(x: str) -> str:
    parts = x.split(';')
    for part in reversed(parts):
        if part:
            return part
    return ''