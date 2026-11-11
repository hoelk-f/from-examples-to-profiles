(define-fun f ((x String)) String (list.at (str.split x (str.++ e" " (list.at (str.split x e" ") 5.0))) 0))
