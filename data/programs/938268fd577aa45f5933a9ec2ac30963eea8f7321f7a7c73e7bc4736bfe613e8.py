def transform(x: str) -> str:
    start = x.find('(')
    if start == -1:
        return ''
    end = x.find(')', start + 1)
    if end == -1:
        return ''
    inner = x[start + 1:end]
    first_part = inner.split(';', 1)[0]
    return first_part.strip()