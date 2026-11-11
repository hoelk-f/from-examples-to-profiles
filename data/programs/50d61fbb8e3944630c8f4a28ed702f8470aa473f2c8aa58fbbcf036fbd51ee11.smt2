(define-fun f ((x String)) String (str.substr (str.++ x x) 2 (- (str.indexof x " (" 0) 2)))
