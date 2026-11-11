import urllib.parse

def transform(x: str) -> str:
    parsed = urllib.parse.urlparse(x)
    return parsed.path if parsed.path else '/'