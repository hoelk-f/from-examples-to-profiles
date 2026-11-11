def transform(x: str) -> str:
    segments = [s for s in x.split('.') if s]
    n = len(segments)
    keep = max(n - 2, 0)
    result = '.'.join(segments[-keep:]) if keep > 0 else ''
    return result + '.'
