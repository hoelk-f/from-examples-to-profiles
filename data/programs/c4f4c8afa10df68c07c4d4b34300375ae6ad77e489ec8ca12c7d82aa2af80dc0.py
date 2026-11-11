def transform(x: str) -> str:
    start = x.find('(')
    if start == -1:
        return ''
    start += 1
    end_semicolon = x.find(';', start)
    end_paren = x.find(')', start)
    if end_semicolon != -1 and (end_paren == -1 or end_semicolon < end_paren):
        end = end_semicolon
    elif end_paren != -1:
        end = end_paren
    else:
        end = len(x)
    return x[start:end].strip()