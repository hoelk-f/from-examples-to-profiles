import re

def transform(x: str) -> str:
    x = re.sub(r'^\d+\. ', '', x)
    x = x.split(' - ')[0]
    return x
