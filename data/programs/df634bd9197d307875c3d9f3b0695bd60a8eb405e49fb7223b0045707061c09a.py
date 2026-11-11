import re

def transform(x: str) -> str:
    return re.search(r'<country>(.*?)</country>', x).group(1)
