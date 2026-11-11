def transform(x: str) -> str:
    parts = x.split(",")
    last = parts[-1].strip()
    tokens = last.split()
    return " ".join(tokens[:-2])
