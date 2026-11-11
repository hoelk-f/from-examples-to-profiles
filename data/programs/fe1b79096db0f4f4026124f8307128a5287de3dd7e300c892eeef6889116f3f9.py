import re

def transform(x: str) -> str:
    last_display = ""
    for match in re.finditer(r'\[\[([^]]+)\]\]', x):
        content = match.group(1)
        if "|" in content:
            display = content.split("|")[-1]
        else:
            display = content
        last_display = display
    return last_display