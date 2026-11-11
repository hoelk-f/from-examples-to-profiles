def transform(x: str) -> str:
    start = x.index(". ") + 2
    end = x.index(" - ")
    return x[start:end]
