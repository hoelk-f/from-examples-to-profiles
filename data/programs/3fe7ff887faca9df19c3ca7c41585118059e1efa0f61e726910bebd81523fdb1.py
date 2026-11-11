import re

def transform(x: str) -> str:
    return re.search(r'ask\s+(\S+)\s+for', x).group(1)
