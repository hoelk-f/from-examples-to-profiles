def transform(x: str) -> str:
    start = x.rfind('<')
    end = x.rfind('>')
    if start == -1 or end == -1 or end <= start:
        return ''
    inner = x[start + 1:end]
    parts = inner.split(',')
    return parts[-1] if parts else ''