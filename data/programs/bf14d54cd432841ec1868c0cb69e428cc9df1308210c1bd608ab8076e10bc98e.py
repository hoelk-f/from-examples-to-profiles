def transform(x: str) -> str:
    import re
    return re.search(r'<price>(.*?)</price>', x).group(1)