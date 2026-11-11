import urllib.parse

def transform(x: str) -> str:
    parsed = urllib.parse.urlparse(x)
    path = parsed.path
    return path if path else "/"