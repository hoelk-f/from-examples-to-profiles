def transform(x: str) -> str:
    idx = x.index('+')
    result = ''
    for c in x[idx+1:]:
        if c.isdigit():
            result += c
        else:
            break
    return result
