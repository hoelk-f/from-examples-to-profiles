(define-fun f ((x String)) String (str.substr (str.replace x "day, " "") (str.indexof x " " 0) 5))
