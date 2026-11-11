(define-fun f ((x String)) String (list.at (str.split x (str.retainL (str.head x (int.neg 3)))) 1))
