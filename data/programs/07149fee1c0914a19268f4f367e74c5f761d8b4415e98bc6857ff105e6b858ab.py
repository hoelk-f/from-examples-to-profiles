def transform(x: str) -> str:
    s = x.rstrip()
    if s.endswith(", Italy"):
        s = s[:-7]
    return s[-2:]
