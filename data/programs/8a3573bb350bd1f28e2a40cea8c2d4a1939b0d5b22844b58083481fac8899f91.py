def transform(x: str) -> str:
    tokens = x.split()
    for i, t in enumerate(tokens):
        if t[0].isdigit():
            return " ".join(tokens[:i])
    return x
