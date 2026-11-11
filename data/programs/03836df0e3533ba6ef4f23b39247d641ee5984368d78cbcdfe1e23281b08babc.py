def transform(x: str) -> str:
    tokens = x.split()
    nums = [t for t in tokens if t.isdigit()]
    evens = [int(n) for n in nums if int(n) % 2 == 0]
    return str(max(evens))
