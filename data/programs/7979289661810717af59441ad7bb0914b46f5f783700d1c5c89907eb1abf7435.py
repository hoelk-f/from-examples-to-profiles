import re

def transform(x: str) -> str:
    for token in reversed(x.split()):
        if re.fullmatch(r'\d+(?:\.\d+)*', token):
            return token
    return ""