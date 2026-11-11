def transform(x: str) -> str:
    start = x.find('{')
    end = x.rfind('}')
    if 0 <= start < end:
        return x[start + 1:end]
    return ""