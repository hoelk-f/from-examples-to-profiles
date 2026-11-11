def transform(x: str) -> str:
    start = x.find("ask ")
    if start == -1:
        return ""
    start += len("ask ")
    end = x.find(" for", start)
    return x[start:] if end == -1 else x[start:end]