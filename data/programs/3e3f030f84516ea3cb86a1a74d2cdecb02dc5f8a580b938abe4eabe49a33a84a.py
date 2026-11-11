def transform(x: str) -> str:
    from urllib.parse import urlparse

    parsed = urlparse(x)
    path = parsed.path
    if not path.startswith("/"):
        path = "/" + path
    if not path.endswith("/"):
        path = path + "/"
    return path