def transform(x: str) -> str:
    idx = x.index('+') + 1
    result = ''
    for c in x[idx:]:
        if c.isdigit():
            result += c
        else:
            break
    return result
