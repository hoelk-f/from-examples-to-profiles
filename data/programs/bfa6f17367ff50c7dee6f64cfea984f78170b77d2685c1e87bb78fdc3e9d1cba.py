import re

def transform(x: str) -> str:
    return re.sub(r'^\d+\. ', '', re.sub(r', \$[\d.]+$', '', x))
