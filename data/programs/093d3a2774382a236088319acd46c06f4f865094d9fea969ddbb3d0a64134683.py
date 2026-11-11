import urllib.parse

def transform(x: str) -> str:
    parsed = urllib.parse.urlparse(x)
    path = parsed.path
    if not path:
        return "/"
    if not path.startswith("/"):
        path = "/" + path
    if not path.endswith("/"):
        path = path + "/"
    return path