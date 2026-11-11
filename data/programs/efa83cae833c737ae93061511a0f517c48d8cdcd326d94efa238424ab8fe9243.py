def transform(x: str) -> str:
    s = x[1:-1] if x.startswith('<') and x.endswith('>') else x
    if s.endswith('.h'):
        s = s[:-2]
    return s
