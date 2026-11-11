def transform(x: str) -> str:
    # Find the first occurrence of a dot followed by a space
    after_dot = x.partition('. ')[2]
    if not after_dot:
        # If not found, return the original string stripped
        return x.strip()
    # Split at the first occurrence of ' -'
    before_dash = after_dot.partition(' -')[0]
    return before_dash.strip()