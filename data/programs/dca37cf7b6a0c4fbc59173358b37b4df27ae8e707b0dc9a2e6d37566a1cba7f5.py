def transform(x: str) -> str:
    if "=" in x:
        return x.split("=", 1)[1].strip()
    return x.strip()