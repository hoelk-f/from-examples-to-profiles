def transform(x: str) -> str:
    # Replace the first '=' with ':' to form a proper scheme delimiter
    y = x.replace('=', ':', 1)
    # Locate the "://"
    i = y.find('://')
    # Return the part after the delimiter if present
    return y[i + 3 :] if i != -1 else y