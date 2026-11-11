def transform(x: str) -> str:
    from urllib.parse import urlparse
    return urlparse(x).path