import urllib.parse

def transform(x: str) -> str:
    """
    Extract the path component of a URL, preserving the leading and trailing slashes.
    """
    path = urllib.parse.urlparse(x).path
    # Ensure the path starts with a slash
    if not path.startswith("/"):
        path = "/" + path
    # Ensure the path ends with a slash (if it was present in the original URL)
    if not path.endswith("/") and urllib.parse.urlparse(x).path.endswith("/"):
        path += "/"
    return path