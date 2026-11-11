def transform(x: str) -> str:
    # Remove surrounding angle brackets if present
    if x.startswith("<") and x.endswith(">"):
        x = x[1:-1]
    # Return the part before the first dot, if any
    return x.split(".", 1)[0]