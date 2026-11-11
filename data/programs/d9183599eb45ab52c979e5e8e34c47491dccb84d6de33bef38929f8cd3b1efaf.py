def transform(x: str) -> str:
    start = x.rfind('(')
    if start == -1:
        return ''
    end = x.find(')', start)
    if end == -1:
        return ''
    return x[start + 1:end]