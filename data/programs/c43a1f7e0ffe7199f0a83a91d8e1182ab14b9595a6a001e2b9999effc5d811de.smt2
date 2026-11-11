(define-fun f ((x String)) String (str.++ (str.++ (str.retainL (list.at (str.split x e" ") 1.0)) e" ") (str.retainLc (list.at (str.split x e" ") 2.0))))
