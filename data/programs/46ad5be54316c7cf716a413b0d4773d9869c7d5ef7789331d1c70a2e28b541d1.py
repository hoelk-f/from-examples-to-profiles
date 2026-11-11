def transform(x: str) -> str:
    idx = x.index("://") + 3
    slash_idx = x.index("/", idx)
    return x[slash_idx:]
