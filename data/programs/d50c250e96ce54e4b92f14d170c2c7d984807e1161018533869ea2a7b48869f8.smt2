(define-fun f ((x String)) String (str.substr (str.++ (str.++ "24" " ") x) (str.indexof x "(" 0) 2))
