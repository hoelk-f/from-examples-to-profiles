import re

def transform(x: str) -> str:
    pattern = re.compile(r'^\d+(?:\.\d+)?g$')
    for token in x.split():
        if pattern.match(token):
            return token
    return ""