(define-fun f ((x String)) String (str.substr (str.++ x x) 0 (str.indexof x "," 0)))
