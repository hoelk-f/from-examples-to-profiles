def transform(x: str) -> str:
    s = x.strip('<>')
    if '.' in s:
        s = s[:s.rfind('.')]
    return s
