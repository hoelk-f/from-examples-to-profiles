def transform(x: str) -> str:
    start = x.find('<')
    end = x.find('>', start + 1)
    if start == -1 or end == -1:
        return ''
    inner = x[start + 1:end]
    parts = inner.split(',')
    return parts[-1].strip()