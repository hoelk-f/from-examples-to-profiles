(define-fun f ((x String)) String (str.substr (str.replace x " Jane " "") (str.indexof x " " 0) 5))
