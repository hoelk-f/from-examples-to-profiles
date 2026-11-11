import re

def transform(x: str) -> str:
    years = re.findall(r'\b\d{4}\b', x)
    return ', '.join(years)