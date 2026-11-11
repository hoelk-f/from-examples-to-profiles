def transform(x: str) -> str:
    start = x.rfind("(")
    end = x.rfind(")")
    return x[start+1:end]
