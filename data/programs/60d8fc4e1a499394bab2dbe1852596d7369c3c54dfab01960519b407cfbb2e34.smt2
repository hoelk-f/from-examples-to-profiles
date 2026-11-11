(define-fun f ((x String)) String (str.substr (str.replace x " " "") (str.indexof x " S" 0) 5))
