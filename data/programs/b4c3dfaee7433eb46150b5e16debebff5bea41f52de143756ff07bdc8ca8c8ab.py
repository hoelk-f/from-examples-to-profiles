def transform(x: str) -> str:
    start = x.find('>') + 1
    end = x.rfind('<')
    if start == 0 or end == -1 or start >= end:
        return x
    return x[start:end]