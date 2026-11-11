def transform(x: str) -> str:
    idx = x.index("@") + 1
    rest = x[idx:]
    space_idx = rest.find(" ")
    if space_idx == -1:
        return rest
    return rest[:space_idx]