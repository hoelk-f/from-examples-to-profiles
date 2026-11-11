import re

def transform(x: str) -> str:
    for token in x.split():
        if re.fullmatch(r'\d+,\d+', token):
            return token
    return ""