def transform(x: str) -> str:
    return x.replace(' ', '-').split('-')[2]
