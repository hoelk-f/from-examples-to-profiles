def transform(x: str) -> str:
    x = x.replace("<strong>", "").replace("</strong>", "").replace("&pound;", "")
    return x