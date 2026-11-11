import urllib.parse

def transform(x: str) -> str:
    path = urllib.parse.urlparse(x).path
    if not path.startswith('/'):
        path = '/' + path
    if not path.endswith('/'):
        path = path + '/'
    return path