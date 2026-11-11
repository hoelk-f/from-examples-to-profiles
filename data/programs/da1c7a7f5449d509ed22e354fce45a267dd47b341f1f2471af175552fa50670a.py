def transform(x: str) -> str:
    # Remove the leading numbered prefix ending with ". "
    _, _, after_prefix = x.partition('. ')
    # Take the part before the " - " separator
    first_part, _, _ = after_prefix.partition(' - ')
    return first_part.strip()