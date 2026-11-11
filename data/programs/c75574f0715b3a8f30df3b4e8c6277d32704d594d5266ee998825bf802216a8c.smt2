(define-fun f ((x String)) String (str.substr (str.replace x ", " "") (str.indexof x "A " 0) 5))
