(define-fun f ((x String)) String (list.at (str.split x (list.at (str.split x (int.to.str 1)) (int.neg 5))) 1))
