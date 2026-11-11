def transform(x: str) -> str:
    return x.split("Model: ")[-1].strip()