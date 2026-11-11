import html
import re

def transform(x: str) -> str:
    x = re.sub(r'<[^>]+>', '', x)
    x = html.unescape(x)
    return ''.join(c for c in x if c.isdigit() or c == ',')
