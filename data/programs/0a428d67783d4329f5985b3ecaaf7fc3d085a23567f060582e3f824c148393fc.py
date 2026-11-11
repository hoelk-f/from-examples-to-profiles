def transform(x: str) -> str:
    start = x.rfind('(')
    end = x.rfind(')')
    if start != -1 and end != -1 and end > start:
        return x[start + 1:end]
    return ""