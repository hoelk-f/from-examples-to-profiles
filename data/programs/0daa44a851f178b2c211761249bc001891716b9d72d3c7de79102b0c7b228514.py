def transform(x: str) -> str:
    prefix = "ask "
    suffix = " for"
    start = x.find(prefix)
    if start == -1:
        return ""
    start += len(prefix)
    end = x.find(suffix, start)
    if end == -1:
        end = len(x)
    return x[start:end]