def transform(x: str) -> str:
    return x.split(";")[1].split(",")[0].strip()
