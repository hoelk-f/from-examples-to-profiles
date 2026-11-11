(define-fun f ((x String)) String (str.substr (str.++ " " x) (str.indexof x "A " 0) 2))
