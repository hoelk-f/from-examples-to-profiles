(define-fun f ((x String)) String (str.substr (str.replace x " " "ber,19") (str.indexof x "(" 0) 4))
