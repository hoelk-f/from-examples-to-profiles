(define-fun f ((x String)) String (str.++ (str.++ (list.at (str.split x e" ") (float.+ 1.0 5.0)) e" ") (str.retainL (list.at (str.split x e" ") (float.neg 2.0)))))
