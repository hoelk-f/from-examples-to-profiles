def transform(x: str) -> str:
    idx = x.rfind(", Italy")
    before = x[:idx]
    last_space = before.rfind(" ")
    return before[last_space + 1:]
