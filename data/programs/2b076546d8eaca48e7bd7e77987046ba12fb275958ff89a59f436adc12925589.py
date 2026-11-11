def transform(x: str) -> str:
    last_open = x.rfind('(')
    if last_open == -1:
        return ''
    close = x.find(')', last_open)
    if close == -1:
        return ''
    return x[last_open + 1:close]