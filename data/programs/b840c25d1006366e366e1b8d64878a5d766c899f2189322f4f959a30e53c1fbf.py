import urllib.parse

def transform(x: str) -> str:
    """
    Extracts the path component from a URL, preserving leading and trailing slashes.
    """
    parsed = urllib.parse.urlparse(x)
    return parsed.path or "/"