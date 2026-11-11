import re

FENCE = re.compile(
    r'[ \t\r\n]*```(?P<language>python|py)?[ \t]*\r?\n'
    r'(?P<code>.*?)^```[ \t]*(?:\r?\n[ \t\r\n]*)?\Z',
    re.MULTILINE | re.DOTALL | re.IGNORECASE)

def extract(answer):
    """Remove only one outer fence. Preserve the exact interior substring."""
    match = FENCE.fullmatch(answer)
    if match and not re.search(r'(?m)^[ \t]*```', match['code']):
        return match['code'], {'rule': 'single_python_fence',
            'language': (match['language'] or '').lower(), 'span': list(match.span('code'))}
    return answer, {'rule': 'unchanged', 'span': [0, len(answer)]}
