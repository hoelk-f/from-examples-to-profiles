(define-fun f ((x String)) String (str.substr (str.replace (str.++ x "Vienna") "Vienna" " 4 196") (str.indexof (str.++ x "Milan") "Milan" 0) (str.indexof x " " 0)))
