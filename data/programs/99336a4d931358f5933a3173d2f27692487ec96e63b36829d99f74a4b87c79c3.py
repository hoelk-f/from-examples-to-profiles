def transform(x: str) -> str:
    return x.strip().split()[0] if x.strip() else ""