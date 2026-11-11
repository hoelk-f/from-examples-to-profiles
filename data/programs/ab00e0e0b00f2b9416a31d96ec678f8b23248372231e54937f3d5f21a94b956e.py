def transform(x: str) -> str:
    start = x.index('<') + 1
    end = x.index('>')
    name = x[start:end].split('/')[-1]
    if name.endswith('.h'):
        name = name[:-2]
    return name
