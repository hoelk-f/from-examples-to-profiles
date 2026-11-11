def transform(x: str) -> str:
    # Split on '/' and take the part after it
    after_slash = x.split('/')[-1]
    # Split on the first '-' and take the part after it
    return after_slash.split('-', 1)[-1]