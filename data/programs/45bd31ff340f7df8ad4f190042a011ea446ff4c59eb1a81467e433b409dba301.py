def transform(x: str) -> str:
    eq_idx = x.index("=")
    space_idx = x.index(" ", eq_idx)
    return x[space_idx + 1:]
