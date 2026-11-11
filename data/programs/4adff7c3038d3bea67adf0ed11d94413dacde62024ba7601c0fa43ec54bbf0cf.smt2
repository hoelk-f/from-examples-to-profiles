(define-fun f ((x String)) String (list.at (str.split x (list.at (str.split x (str.tail x -1.0)) 2.0)) 1))
