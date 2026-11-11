def transform(x: str) -> str:
    from urllib.parse import urlparse
    path = urlparse(x).path
    if not path.startswith("/"):
        path = "/" + path
    if not path.endswith("/"):
        path = path + "/"
    return path