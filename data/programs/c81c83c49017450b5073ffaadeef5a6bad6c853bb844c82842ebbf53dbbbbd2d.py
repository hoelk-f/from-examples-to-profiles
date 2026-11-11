def transform(x: str) -> str:
    start = x.find('(')
    end = x.find(')', start + 1)
    if start != -1 and end != -1:
        return x[start + 1 : end].strip()
    return ""