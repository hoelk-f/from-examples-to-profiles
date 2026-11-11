def transform(x: str) -> str:
    # Extract the substring before "(latitude)" and clean up trailing punctuation/spaces
    before = x.split("(latitude)")[0]
    return before.rstrip(" ,")