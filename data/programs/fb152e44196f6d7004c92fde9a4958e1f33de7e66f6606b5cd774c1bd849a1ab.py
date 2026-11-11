def transform(x: str) -> str:
    at_idx = x.index('@')
    rest = x[at_idx + 1:]
    space_idx = rest.find(' ')
    if space_idx == -1:
        return rest
    return rest[:space_idx]
