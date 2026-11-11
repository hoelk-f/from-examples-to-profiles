(define-fun f ((x String)) String (str.++ (str.head (str.tail x 1.0) 5.0) (str.retainN (str.tail x -1.0))))
