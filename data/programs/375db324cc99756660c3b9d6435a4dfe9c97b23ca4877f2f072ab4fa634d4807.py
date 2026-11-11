def transform(x: str) -> str:
    start = x.index("''[[") + 4
    end = x.index("]]''", start)
    inner = x[start:end]
    if "|" in inner:
        return inner.rsplit("|", 1)[1]
    return inner
