def transform(x: str) -> str:
    tokens = x.split()
    numeric = [int(t) for t in tokens if t.isdigit()]
    numeric.sort(reverse=True)
    return str(numeric[1])
