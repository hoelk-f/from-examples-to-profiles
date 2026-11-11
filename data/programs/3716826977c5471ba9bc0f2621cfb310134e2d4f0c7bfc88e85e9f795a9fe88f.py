def transform(x: str) -> str:
    s = x.strip('<>')
    if s.endswith('.h'):
        s = s[:-2]
    return s
