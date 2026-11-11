def transform(x: str) -> str:
    tokens = x.split()
    numeric = [t for t in tokens if t.isdigit()]
    numeric.sort(key=int, reverse=True)
    return numeric[1] if len(numeric) > 1 else numeric[0]
