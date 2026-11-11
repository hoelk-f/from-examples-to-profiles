def transform(x: str) -> str:
    idx = x.rfind('(')
    if idx != -1:
        end = idx
        if end > 0 and x[end - 1] == ' ':
            end -= 1
        return x[:end].rstrip()
    return x.rstrip()