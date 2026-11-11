def transform(x: str) -> str:
    words = x.split()
    return max(words, key=len)
