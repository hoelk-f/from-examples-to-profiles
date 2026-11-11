def transform(x: str) -> str:
    start = x.find('<')
    end = x.find('>', start + 1)
    if start == -1 or end == -1:
        return ""
    header = x[start + 1:end]
    return header.split('.')[0]