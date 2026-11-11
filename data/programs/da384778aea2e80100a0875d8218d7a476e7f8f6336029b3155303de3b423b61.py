def transform(x: str) -> str:
    _, _, tail = x.rpartition(';')
    return tail.strip()
