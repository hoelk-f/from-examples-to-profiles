(define-fun f ((x String)) String (str.substr (str.++ x x) 3 (+ (str.indexof x "November" 0) 5)))
