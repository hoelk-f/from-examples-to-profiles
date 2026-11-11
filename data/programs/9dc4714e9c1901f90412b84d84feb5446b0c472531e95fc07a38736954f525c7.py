def transform(x: str) -> str:
    # Remove leading '<' and trailing '>' if present
    if x.startswith("<") and x.endswith(">"):
        x = x[1:-1]
    # Split on '.' and take the first part
    return x.split(".", 1)[0]