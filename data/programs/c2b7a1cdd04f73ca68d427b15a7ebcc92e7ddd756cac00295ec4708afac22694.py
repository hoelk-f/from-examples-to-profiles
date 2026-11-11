def transform(x: str) -> str:
    s = x[1:-1]
    if s.endswith('.h'):
        s = s[:-2]
    return s
