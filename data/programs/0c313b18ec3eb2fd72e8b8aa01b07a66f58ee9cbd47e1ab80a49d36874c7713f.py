def transform(x: str) -> str:
    idx = x.find('@')
    if idx == -1:
        return ""
    rest = x[idx + 1:]
    for i, ch in enumerate(rest):
        if ch.isspace():
            return rest[:i]
    return rest
