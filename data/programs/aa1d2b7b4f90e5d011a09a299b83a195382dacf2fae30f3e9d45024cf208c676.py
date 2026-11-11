import re

def transform(x: str) -> str:
    m = re.match(r'^\d+\.\s+(.*)', x)
    if m:
        result = m.group(1)
    else:
        result = x
    if ' - ' in result:
        result = result.split(' - ')[0]
    return result
