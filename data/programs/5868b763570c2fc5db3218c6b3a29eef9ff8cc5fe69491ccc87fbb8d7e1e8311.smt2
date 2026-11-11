(define-fun f ((x String)) String (str.++ (str.tail (list.at (str.split x (int.to.str 5)) 2) 1) (list.at (str.split x (list.at (str.split x (int.to.str 5)) 2)) -1)))
