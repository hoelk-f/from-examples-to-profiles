import re

def transform(x: str) -> str:
    matches = re.findall(r'\[\[(.*?)\]\]', x)
    if len(matches) >= 2:
        result = matches[1]
        if '|' in result:
            result = result.split('|')[-1]
        return result
    return x
