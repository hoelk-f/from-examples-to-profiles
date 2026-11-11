def transform(x: str) -> str:
    for i, ch in enumerate(x):
        if ch.isdigit():
            return x[:i].rstrip()
    return x
