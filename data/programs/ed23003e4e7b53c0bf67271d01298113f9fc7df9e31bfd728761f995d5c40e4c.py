def transform(x: str) -> str:
    idx = x.find('(')
    if idx != -1:
        # Remove any preceding space before '('
        if idx > 0 and x[idx - 1] == ' ':
            idx -= 1
        x = x[:idx]
    return x.rstrip()