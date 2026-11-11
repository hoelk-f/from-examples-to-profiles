def transform(x: str) -> str:
    import re
    return re.search(r',(\d{4})', x).group(1)