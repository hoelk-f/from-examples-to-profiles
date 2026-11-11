import urllib.parse

def transform(x: str) -> str:
    """
    Extracts the path component from a URL, preserving leading and trailing slashes.
    """
    return urllib.parse.urlparse(x).path or "/"