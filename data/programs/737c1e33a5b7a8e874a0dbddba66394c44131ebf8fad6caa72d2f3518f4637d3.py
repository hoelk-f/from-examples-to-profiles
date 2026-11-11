def transform(x: str) -> str:
    start = x.find("''[[")
    end = x.find("]]''", start)
    inner = x[start + 4:end]
    if "|" in inner:
        return inner.split("|")[-1]
    return inner
