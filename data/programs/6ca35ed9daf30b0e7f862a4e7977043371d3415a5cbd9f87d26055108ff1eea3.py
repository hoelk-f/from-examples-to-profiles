def transform(x: str) -> str:
    tokens = x.split()
    nums = [t for t in tokens if t.isdigit()]
    nums.sort(key=int)
    return str(nums[-2])
