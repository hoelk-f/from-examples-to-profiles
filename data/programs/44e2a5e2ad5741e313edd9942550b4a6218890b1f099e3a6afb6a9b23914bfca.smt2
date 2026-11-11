(define-fun f ((x String)) String (str.substr (str.++ x x) 3 (- (str.indexof x "," 0) 3)))
