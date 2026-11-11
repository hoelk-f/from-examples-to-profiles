import re
import html

def transform(x: str) -> str:
    x = re.sub(r'<[^>]+>', '', x)
    x = html.unescape(x)
    x = x.replace('\u00a3', '')
    return x
