(define-fun f ((x String)) String (str.++ (str.++ (str.retainLc (list.at (str.split x e" ") (float.neg 2.0))) e" ") (str.retainL (list.at (str.split x e" ") -1.0))))
