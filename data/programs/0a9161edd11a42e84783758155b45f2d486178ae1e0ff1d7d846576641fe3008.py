def transform(x: str) -> str:
    nums = sorted([int(tok) for tok in x.split() if tok.isdigit()], reverse=True)
    return str(nums[1])
