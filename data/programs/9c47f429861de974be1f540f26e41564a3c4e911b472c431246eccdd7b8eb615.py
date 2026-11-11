def transform(x: str) -> str:
    parts = x.split(",")
    return parts[1].strip().split()[-1]