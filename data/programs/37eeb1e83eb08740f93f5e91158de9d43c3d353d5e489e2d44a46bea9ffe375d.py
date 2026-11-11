def transform(x: str) -> str:
    idx = x.index('@')
    rest = x[idx + 1:]
    space_idx = rest.find(' ')
    if space_idx == -1:
        return rest
    return rest[:space_idx]