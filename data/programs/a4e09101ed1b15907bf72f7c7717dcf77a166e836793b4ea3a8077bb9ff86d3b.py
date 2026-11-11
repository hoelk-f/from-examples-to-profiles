import os

def transform(x: str) -> str:
    return os.path.dirname(x) + "/"
