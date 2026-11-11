def transform(x: str) -> str:
    for i, c in enumerate(x):
        if not c.isdigit():
            return x[:i]
    return x
