def transform(x: str) -> str:
    _, sep, after = x.partition('aka')
    return after.lstrip() if sep else x