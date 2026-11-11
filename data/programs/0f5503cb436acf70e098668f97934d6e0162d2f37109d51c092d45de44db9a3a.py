def transform(x: str) -> str:
    start = x.find('(')
    if start == -1:
        return ''
    end = x.find(')', start + 1)
    if end == -1:
        return ''
    return x[start + 1:end]