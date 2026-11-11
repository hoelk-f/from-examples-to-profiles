def transform(x: str) -> str:
    first = x.find('.')
    if first == -1:
        return ''
    second = x.find('.', first + 1)
    if second == -1:
        return ''
    return x[second + 1:]