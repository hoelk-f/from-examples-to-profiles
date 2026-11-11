def transform(x: str) -> str:
    """
    Extracts the first component of the domain part of an email address.
    For example, given "user@sub.example.com" it returns "sub".
    """
    at_index = x.find('@')
    if at_index == -1:
        return ''
    start = at_index + 1
    dot_index = x.find('.', start)
    if dot_index == -1:
        return x[start:]
    return x[start:dot_index]