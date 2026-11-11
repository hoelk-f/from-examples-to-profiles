def transform(x: str) -> str:
    s = x.replace(", Italy", "").strip()
    return s.split()[-1]
