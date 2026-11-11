def transform(x: str) -> str:
    # Split on '/', take the part after the last slash
    second_part = x.split('/')[-1]
    # Split on '-', take the part after the last dash
    return second_part.rsplit('-', 1)[-1]