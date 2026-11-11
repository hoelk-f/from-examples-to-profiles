import re

def transform(x: str) -> str:
    hashtags = re.findall(r'#\w+', x)
    return hashtags[-1] if hashtags else ''