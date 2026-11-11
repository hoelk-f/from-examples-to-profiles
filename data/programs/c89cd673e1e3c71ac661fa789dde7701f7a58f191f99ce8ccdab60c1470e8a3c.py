def transform(x: str) -> str:
    s = x.strip()
    return s.split()[-1] if s else ""