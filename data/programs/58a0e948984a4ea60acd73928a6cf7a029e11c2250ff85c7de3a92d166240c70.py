def transform(x: str) -> str:
    return x[len("ask "):len(x)-len(" for all support requests")]
