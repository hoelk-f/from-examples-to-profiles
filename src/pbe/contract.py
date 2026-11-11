class OutsideContract(ValueError):
    pass

def locate(s, marker, last=False):
    p = s.rfind(marker) if last else s.find(marker)
    if not marker or p < 0:
        raise OutsideContract('Required marker absent: ' + repr(marker))
    return p

def tokens(s, d):
    if not d:
        raise OutsideContract('Empty delimiter')
    start = 0
    out = []
    while True:
        p = s.find(d, start)
        if p < 0:
            out.append((start, len(s)))
            return out
        out.append((start, p))
        start = p + len(d)

def extract(text, selector):
    start, end = (0, len(text))
    for op in selector:
        s = text[start:end]
        k = op[0]
        lo, hi = (0, len(s))
        try:
            if k == 'trim':
                lo = len(s) - len(s.lstrip())
                hi = len(s.rstrip())
            elif k in ('token', 'token_span'):
                spans = tokens(s, op[1])
                lo = spans[op[2]][0]
                hi = spans[op[2] if k == 'token' else op[3]][1]
            elif k == 'containing_token':
                matches = [(a, b) for a, b in tokens(s, op[1]) if op[2] in s[a:b]]
                if len(matches) != 1:
                    raise OutsideContract('Marker must identify one token')
                lo, hi = matches[0]
            elif k == 'from_after_marker_to_next_inclusive':
                p = locate(s, op[1]) + len(op[1])
                lo = p + locate(s[p:], op[2])
            elif k == 'before_nth':
                p = locate(s, op[4]) + len(op[4])
                for _ in range(op[2]):
                    hi = p + locate(s[p:], op[1])
                    p = hi + len(op[1])
            elif k in ('before', 'after', 'before_last', 'after_last', 'before_inclusive', 'after_inclusive', 'before_last_inclusive'):
                p = locate(s, op[1], 'last' in k)
                if k.startswith('before'):
                    hi = p + (len(op[1]) if 'inclusive' in k else 0)
                else:
                    lo = p + (0 if 'inclusive' in k else len(op[1]))
            else:
                raise ValueError('Unknown selector operation ' + k)
        except IndexError as e:
            raise OutsideContract('Requested field position absent') from e
        if hi < lo:
            raise OutsideContract('Reversed or empty trimmed range')
        end = start + hi
        start += lo
    if start == end:
        raise OutsideContract('Core contract requires a present nonempty field')
    return (text[start:end], (start, end))
