def transform(x: str) -> str:
    parts = x.split(',')
    if len(parts) < 2:
        return ''
    middle = parts[1].strip()
    tokens = middle.split()
    return tokens[-1] if tokens else ''