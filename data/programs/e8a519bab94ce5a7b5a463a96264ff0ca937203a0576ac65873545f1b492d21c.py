def transform(x: str) -> str:
    """
    Return the substring after the last period in the input string.
    If there is no period, return an empty string.
    """
    if '.' not in x:
        return ''
    return x.rsplit('.', 1)[1]