def transform(x: str) -> str:
    # Remove surrounding angle brackets if present
    if x.startswith("<") and x.endswith(">"):
        x = x[1:-1]
    # Split at the first dot and take the first segment
    return x.split(".", 1)[0]