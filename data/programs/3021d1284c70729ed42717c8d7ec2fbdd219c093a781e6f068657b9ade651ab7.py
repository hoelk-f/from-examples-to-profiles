import urllib.parse

def transform(x: str) -> str:
    """
    Extracts the path component from a URL, preserving the leading and trailing slashes.
    If the URL has no explicit path, returns '/'.
    """
    parsed = urllib.parse.urlparse(x)
    path = parsed.path
    return path if path else "/"