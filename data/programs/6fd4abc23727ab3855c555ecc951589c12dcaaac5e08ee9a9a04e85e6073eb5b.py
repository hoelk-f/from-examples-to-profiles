def transform(x: str) -> str:
    # Remove leading number and dot-space
    _, _, rest = x.partition('. ')
    # Extract title before the comma and price
    title, _, _ = rest.partition(', $')
    return title