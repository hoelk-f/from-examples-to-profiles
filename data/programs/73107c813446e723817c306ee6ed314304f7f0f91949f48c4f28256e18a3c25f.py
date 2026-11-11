import re

_months = ("January|February|March|April|May|June|July|August|September|October|November|December")
_pattern = re.compile(rf'({ _months}) \d{{1,2}}(?:-\d{{1,2}})?, \d{{4}}')

def transform(x: str) -> str:
    m = _pattern.search(x)
    return m.group(0) if m else ""