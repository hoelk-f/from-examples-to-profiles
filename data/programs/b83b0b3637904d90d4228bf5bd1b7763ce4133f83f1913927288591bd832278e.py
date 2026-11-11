import urllib.parse

def transform(x: str) -> str:
    path = urllib.parse.urlparse(x).path
    if not path:
        return "/"
    # Ensure leading slash
    if not path.startswith("/"):
        path = "/" + path
    # Ensure trailing slash
    if not path.endswith("/"):
        path = path + "/"
    return path