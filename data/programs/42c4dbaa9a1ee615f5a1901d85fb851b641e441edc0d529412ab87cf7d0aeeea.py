def transform(x: str) -> str:
    start = x.find('+')
    if start == -1:
        return ''
    start += 1
    end = start
    while end < len(x) and not x[end].isspace():
        end += 1
    return x[start:end]