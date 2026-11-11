def transform(x: str) -> str:
    start = x.find('<')
    end = x.find('>', start)
    if start == -1 or end == -1:
        return ''
    inner = x[start + 1:end]
    parts = inner.split(',')
    return parts[-1] if parts else ''