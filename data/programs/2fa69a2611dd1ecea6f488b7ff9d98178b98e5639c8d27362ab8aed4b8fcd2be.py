def transform(x: str) -> str:
    if '/' not in x:
        return ''
    dir_part = x.rsplit('/', 1)[0]
    if not dir_part.endswith('/'):
        dir_part += '/'
    return dir_part