import html
import re

def transform(x: str) -> str:
    x = re.sub(r'<[^>]+>', '', x)
    x = html.unescape(x)
    x = re.sub(r'[^0-9,]', '', x)
    return x
