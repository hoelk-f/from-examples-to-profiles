(define-fun f ((x String)) String (str.++ (str.++ (list.at (str.split x e" ") 0) e" ") (list.at (str.split x e" ") 1.0)))
