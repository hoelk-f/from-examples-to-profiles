def transform(x: str) -> str:
    filename = x.split()[-1]
    return filename.rsplit('.', 1)[-1]
