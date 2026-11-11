import urllib.parse

def transform(x: str) -> str:
    """
    Extracts and returns the path component of a URL, preserving leading and trailing slashes.
    """
    parsed = urllib.parse.urlparse(x)
    return parsed.path or "/"