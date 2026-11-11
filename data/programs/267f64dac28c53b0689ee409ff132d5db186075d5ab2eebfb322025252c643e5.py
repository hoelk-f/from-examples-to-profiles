def transform(x: str) -> str:
    start = x.find('(')
    if start == -1:
        return ''
    end = x.find(')', start + 1)
    if end == -1:
        return ''
    inside = x[start + 1:end]
    return inside.split(';')[0].strip()