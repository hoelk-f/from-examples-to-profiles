import re

def transform(x: str) -> str:
    tokens = x.split()
    pure_numbers = [int(t) for t in tokens if t.isdigit()]
    even_numbers = [n for n in pure_numbers if n % 2 == 0]
    return str(max(even_numbers))
