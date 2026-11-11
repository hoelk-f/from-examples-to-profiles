(define-fun f ((x String)) String (str.++ (list.at (str.split x (list.at (str.split x (int.to.str 1)) 1)) -1) (list.at (str.split x (list.at (str.split x (int.to.str 5)) 1)) -1)))
