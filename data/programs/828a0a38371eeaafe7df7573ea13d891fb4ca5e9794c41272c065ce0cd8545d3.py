def transform(x: str) -> str:
    last_part = x.rsplit(',', 1)[-1].strip()
    return last_part.split()[0]
