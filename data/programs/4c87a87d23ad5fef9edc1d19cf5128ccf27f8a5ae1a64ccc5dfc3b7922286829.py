def transform(x: str) -> str:
    try:
        start = x.index("@") + 1
    except ValueError:
        return ""
    end = len(x)
    for i, ch in enumerate(x[start:], start):
        if ch.isspace():
            end = i
            break
    return x[start:end]