def transform(x: str) -> str:
    at = x.find('@')
    if at == -1:
        return ''
    domain = x[at + 1 :]
    return domain.split('.')[0]