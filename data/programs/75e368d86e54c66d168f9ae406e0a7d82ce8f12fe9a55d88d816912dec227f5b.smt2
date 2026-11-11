(define-fun f ((x String)) String (str.++ (str.++ (str.tail (list.at (str.split x e" ") 3) 1.0) e" ") (str.retainLl (list.at (str.split x e" ") -1.0))))
