def transform(x: str) -> str:
    tokens = x.split()
    for i in range(1, len(tokens)):
        if len(tokens[i]) == 3 and tokens[i].isalpha():
            return tokens[i - 1] + " " + tokens[i]
    return x
