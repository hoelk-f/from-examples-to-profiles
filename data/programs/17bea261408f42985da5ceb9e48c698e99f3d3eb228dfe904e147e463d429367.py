def transform(x: str) -> str:
    idx = x.rfind('|')
    if idx == -1:
        return x
    end = x.find(']]', idx)
    if end == -1:
        return x[idx + 1:]
    return x[idx + 1:end]
