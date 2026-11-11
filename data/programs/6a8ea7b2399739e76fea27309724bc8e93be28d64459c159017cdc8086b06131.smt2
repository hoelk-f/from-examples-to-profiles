(define-fun f ((x String)) String (str.++ (list.at (str.split x (str.head (str.++ x x) (float.shl10 5.0 1))) 0.0) (list.at (str.split x (list.at (str.split x (str.head x 1.0)) 5.0)) -1.0)))
