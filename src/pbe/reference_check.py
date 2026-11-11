class Invalid(ValueError):
    pass

def evaluate(text, selector):
    current = text
    origin = list(range(len(text)))
    for op in selector:
        kind, *args = op
        left, right = (0, len(current))
        if kind == 'trim':
            while left < right and current[left].isspace():
                left += 1
            while right > left and current[right - 1].isspace():
                right -= 1
        elif kind in ('token', 'token_span', 'containing_token'):
            delimiter = args[0]
            if not delimiter:
                raise Invalid('Empty delimiter')
            pieces = current.split(delimiter)
            offsets, cursor = ([], 0)
            for piece in pieces:
                offsets.append((cursor, cursor + len(piece)))
                cursor += len(piece) + len(delimiter)
            try:
                if kind == 'containing_token':
                    selected = [i for i, p in enumerate(pieces) if args[1] in p]
                    if len(selected) != 1:
                        raise Invalid('Nonunique containing token')
                    left, right = offsets[selected[0]]
                else:
                    left = offsets[args[1]][0]
                    right = offsets[args[1] if kind == 'token' else args[2]][1]
            except IndexError as error:
                raise Invalid('Missing field') from error
        elif kind == 'from_after_marker_to_next_inclusive':
            head, marker, tail = current.partition(args[0])
            if not marker:
                raise Invalid('Missing anchor')
            between, marker2, rest = tail.partition(args[1])
            if not marker2:
                raise Invalid('Missing next marker')
            left = len(head) + len(marker) + len(between)
        elif kind in ('before', 'after', 'before_last', 'after_last', 'before_inclusive', 'after_inclusive', 'before_last_inclusive'):
            if not args[0]:
                raise Invalid('Empty marker')
            head, marker, tail = current.rpartition(args[0]) if 'last' in kind else current.partition(args[0])
            if not marker:
                raise Invalid('Missing marker')
            if kind.startswith('before'):
                right = len(head) + (len(marker) if 'inclusive' in kind else 0)
            else:
                left = len(head) + (0 if 'inclusive' in kind else len(marker))
        else:
            raise ValueError('Unsupported operation: ' + kind)
        if right < left:
            raise Invalid('Reversed span')
        current, origin = (current[left:right], origin[left:right])
    if not current:
        raise Invalid('Empty selected field')
    assert origin == list(range(origin[0], origin[-1] + 1))
    return (current, (origin[0], origin[-1] + 1))
GOLDEN = [('a@b@c', [['before', '@']], 'a'), ('a@b@c', [['after', '@']], 'b@c'), ('a@b@c', [['before_last', '@']], 'a@b'), ('a@b@c', [['after_last', '@']], 'c'), ('a@b@c', [['before_inclusive', '@']], 'a@'), ('a@b@c', [['after_inclusive', '@']], '@b@c'), ('a@b@c', [['before_last_inclusive', '@']], 'a@b@'), ('aaaaX', [['after_last', 'aa']], 'X'), ('aaaaX', [['before_last', 'aa']], 'aa'), ('a::b::c', [['token', '::', 1]], 'b'), ('a::b::c', [['token', '::', -1]], 'c'), ('a::b::c', [['token_span', '::', 0, -2]], 'a::b'), ('a::b::c', [['token_span', '::', -2, -1]], 'b::c'), ('single', [['token', ' ', 0]], 'single'), ('a name_id b', [['containing_token', ' ', '_']], 'name_id'), ('a name_id other_id', [['containing_token', ' ', '_']], None), ('a b c', [['containing_token', ' ', '_']], None), ('a name_id b', [['from_after_marker_to_next_inclusive', '_', ' ']], ' b'), ('prefix<q> A B </q>suffix', [['after', '<q>'], ['before', '</q>'], ['trim']], 'A B'), ('\u2003a\xa0', [['trim']], 'a'), ('pre<é😀>tail', [['after', '<'], ['before', '>']], 'é😀'), ('x', [['before', '@']], None), ('@x', [['before', '@']], None), ('x@', [['after', '@']], None), ('a::b', [['token', '::', 2]], None), ('a::::b', [['token', '::', 1]], None), ('a b c', [['token_span', ' ', 2, 0]], None), ('   ', [['trim']], None), ('a@b', [['before', '']], None)]
