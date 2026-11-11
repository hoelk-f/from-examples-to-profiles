(define-fun f ((x String)) String (str.substr (str.substr x 2 (+ 5 3)) (str.indexof x ";" 0) 5))
