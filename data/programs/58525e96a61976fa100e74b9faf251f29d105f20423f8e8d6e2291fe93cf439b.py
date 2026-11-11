def transform(x: str) -> str:
    # Remove trailing ", France" if present
    suffix = ", France"
    if x.endswith(suffix):
        x = x[: -len(suffix)]
    tokens = x.split()
    for i, token in enumerate(tokens):
        if token.isdigit():
            return " ".join(tokens[:i])
    # Fallback: return stripped string
    return x.strip()