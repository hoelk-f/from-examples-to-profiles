def transform(x: str) -> str:
    i = x.index(". ") + 2
    j = x.rindex(", $")
    return x[i:j]
