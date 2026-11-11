import re

def transform(x: str) -> str:
    # Remove HTML tags
    no_tags = re.sub(r'<[^>]*>', '', x)
    # Remove the pound HTML entity
    result = no_tags.replace('&pound;', '')
    return result.strip()