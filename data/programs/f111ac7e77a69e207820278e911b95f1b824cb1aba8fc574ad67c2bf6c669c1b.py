import re

def transform(x: str) -> str:
    m = re.search(r'\d+am-\d+pm', x)
    return m.group(0) if m else x
