def transform(x: str) -> str:
    """
    Return the file extension of the given filename, i.e., the substring after the
    last period ('.') character. The case of the extension is preserved.
    If the input does not contain a period, an empty string is returned.
    """
    # rpartition splits at the last occurrence of the separator.
    # It returns a tuple: (head, sep, tail). If sep not found, head is '',
    # sep is '', and tail is the original string.
    _, sep, tail = x.rpartition('.')
    return tail if sep else ''