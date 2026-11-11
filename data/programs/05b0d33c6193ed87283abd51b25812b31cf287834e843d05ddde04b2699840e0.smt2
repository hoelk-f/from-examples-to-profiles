(define-fun f ((x String)) String (str.++ (str.++ (list.at (str.split x e" ") 1) e" ") (list.at (str.split x e" ") 2.0)))
