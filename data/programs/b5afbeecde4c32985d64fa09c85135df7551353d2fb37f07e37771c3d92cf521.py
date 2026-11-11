def transform(x: str) -> str:
    dot_space = x.find(". ")
    dash = x.find(" - ", dot_space)
    return x[dot_space + 2:dash]
