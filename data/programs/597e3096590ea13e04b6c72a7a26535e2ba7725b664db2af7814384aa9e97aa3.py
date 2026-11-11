def transform(x: str) -> str:
    """
    Return the file extension of the given filename, without the leading dot.
    The case of the extension is preserved.
    If there is no dot in the input, an empty string is returned.
    """
    # rpartition splits at the last occurrence of the separator.
    # It returns a tuple (head, sep, tail). If sep is not found, head is '' and tail is the original string.
    _, sep, tail = x.rpartition('.')
    return tail if sep else ''