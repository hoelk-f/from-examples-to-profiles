def transform(x: str) -> str:
    parts = x.split(',')
    if not parts:
        return ''
    last = parts[-1].strip()
    tokens = last.split()
    return tokens[0] if tokens else ''