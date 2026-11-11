def transform(x: str) -> str:
    at = x.find('@')
    if at == -1:
        return ''
    start = at + 1
    dot = x.find('.', start)
    if dot == -1:
        return x[start:]
    return x[start:dot]