(define-fun f ((x String)) String (str.substr (str.replace x " " "K 1") (str.indexof x ":" 0) 5))
