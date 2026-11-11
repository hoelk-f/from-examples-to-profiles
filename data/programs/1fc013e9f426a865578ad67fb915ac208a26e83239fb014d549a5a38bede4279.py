def transform(x: str) -> str:
    first = x.find('.')
    if first == -1:
        return x
    second = x.find('.', first + 1)
    if second == -1:
        return x
    return x[:second]