def transform(x: str) -> str:
    words = x.split()
    result = []
    for w in words:
        if any(c.isdigit() for c in w):
            break
        result.append(w)
    return ' '.join(result)
