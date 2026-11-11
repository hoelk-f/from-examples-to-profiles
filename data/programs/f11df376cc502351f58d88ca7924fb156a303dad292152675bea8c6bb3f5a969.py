import urllib.parse

def transform(x: str) -> str:
    """
    Extracts the path component from a URL, ensuring it starts and ends with '/'.
    """
    parsed = urllib.parse.urlparse(x)
    path = parsed.path or "/"
    if not path.startswith("/"):
        path = "/" + path
    if not path.endswith("/"):
        path += "/"
    return path