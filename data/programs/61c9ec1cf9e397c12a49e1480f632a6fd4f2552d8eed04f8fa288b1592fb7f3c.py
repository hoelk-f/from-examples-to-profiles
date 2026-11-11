def transform(x: str) -> str:
    """
    Return the substring that follows the first occurrence of ' aka '.
    If the marker is not present, return the original string.
    """
    marker = " aka "
    if marker in x:
        _, _, after = x.partition(marker)
        return after
    return x