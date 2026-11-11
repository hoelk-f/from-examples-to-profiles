import urllib.parse

def transform(x: str) -> str:
    return urllib.parse.urlparse(x).path or '/'