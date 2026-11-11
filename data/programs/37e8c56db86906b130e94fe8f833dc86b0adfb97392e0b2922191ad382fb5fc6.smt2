(define-fun f ((x String)) String (str.substr (str.replace x " " "") (str.indexof x " " 5) 5))
