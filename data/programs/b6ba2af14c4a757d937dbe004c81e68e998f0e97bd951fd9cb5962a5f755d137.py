def transform(x: str) -> str:
    """
    Remove the Twitter handle (or any substring starting with a space followed by '@')
    from the input string, returning only the preceding portion.
    """
    # Split on the first occurrence of ' @' and keep the part before it.
    return x.partition(' @')[0]