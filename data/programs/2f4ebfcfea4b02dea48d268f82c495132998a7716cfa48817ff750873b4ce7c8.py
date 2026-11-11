def transform(x: str) -> str:
    import re
    # Remove HTML tags
    s = re.sub(r'<[^>]+>', '', x)
    # Remove the pound HTML entity and surrounding whitespace
    s = s.replace('&pound;', '').strip()
    return s