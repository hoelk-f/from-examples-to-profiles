def transform(x: str) -> str:
    # Find the first period that separates the leading number.
    dot_index = x.find('.')
    if dot_index != -1:
        # Skip the period and any following whitespace.
        after_dot = x[dot_index + 1 :].lstrip()
    else:
        after_dot = x
    # The desired segment ends before the delimiter " -".
    segment = after_dot.split(" -", 1)[0]
    return segment