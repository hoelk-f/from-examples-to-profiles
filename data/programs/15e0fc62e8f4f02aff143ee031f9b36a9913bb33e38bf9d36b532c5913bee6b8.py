def transform(x: str) -> str:
    parts = x.split()
    for i, token in enumerate(parts):
        if token.isdigit():
            return " ".join(parts[:i])
    return x.strip()