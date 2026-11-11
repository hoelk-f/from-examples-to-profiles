def transform(x: str) -> str:
    marker = "=//"
    i = x.find(marker)
    return x[i + len(marker) :] if i != -1 else x