def transform(x: str) -> str:
    if "://" in x:
        x = x.split("://", 1)[1]
    idx = x.find("/")
    if idx == -1:
        return "/"
    return x[idx:]
