def transform(x: str) -> str:
    start = x.find('>') + 1
    end = x.rfind('<')
    return x[start:end] if start > 0 and end > start else x.strip()