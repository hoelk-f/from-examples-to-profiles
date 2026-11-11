def transform(x: str) -> str:
    marker = " inferences"
    idx = x.find(marker)
    if idx != -1:
        return x[:idx].strip()
    return ""