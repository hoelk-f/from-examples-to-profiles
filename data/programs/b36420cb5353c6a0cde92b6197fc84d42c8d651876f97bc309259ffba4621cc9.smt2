(define-fun f ((x String)) String (str.substr (str.replace x " aka " "") (str.indexof x " aka " 0) (str.len x)))
