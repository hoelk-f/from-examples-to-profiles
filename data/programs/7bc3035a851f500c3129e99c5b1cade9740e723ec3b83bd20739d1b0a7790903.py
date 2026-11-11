import re

def transform(x: str) -> str:
    match = re.search(r'CPU in ([0-9]*\.?[0-9]+)', x)
    return match.group(1) if match else ''