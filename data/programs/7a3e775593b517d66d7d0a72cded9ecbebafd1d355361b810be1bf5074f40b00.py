def transform(x: str) -> str:
    at = x.find('@')
    if at == -1:
        return ''
    start = at + 1
    end = start
    while end < len(x) and not x[end].isspace():
        end += 1
    return x[start:end]