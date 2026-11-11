def transform(x: str) -> str:
    # Split the string into whitespace-separated parts, take the first part,
    # and remove a leading '+' if present.
    first_part = x.strip().split()[0]
    return first_part.lstrip('+')