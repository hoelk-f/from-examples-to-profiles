def transform(x: str) -> str:
    _, _, after = x.partition(' ')
    return after.split('-', 1)[0]