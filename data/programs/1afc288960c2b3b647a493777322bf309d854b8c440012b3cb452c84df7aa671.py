from urllib.parse import urlparse

def transform(x: str) -> str:
    return urlparse(x).path
