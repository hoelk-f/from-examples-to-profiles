def transform(x: str) -> str:
    if x.startswith("<b>") and x.endswith("<b>"):
        return x[3:-3]
    return x