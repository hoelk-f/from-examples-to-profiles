def transform(x: str) -> str:
    first = x.find('.')
    last = x.rfind('.')
    if first != -1 and last != -1 and first != last:
        return x[first + 1 : last]
    return ""