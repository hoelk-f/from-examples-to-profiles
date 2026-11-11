def transform(x: str) -> str:
    parts = x.split(";")
    middle = parts[1].strip()
    return middle.split(",")[0].strip()
