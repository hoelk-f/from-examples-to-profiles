def transform(x: str) -> str:
    parts = x.split(',')
    if len(parts) < 2:
        return ''
    second = parts[1]
    second = second.split('(')[0].strip()
    return second