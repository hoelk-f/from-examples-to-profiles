(define-fun f ((x String)) String (str.++ (str.head (str.tail x 3) (float.+ 2.0 (float.shl10 -1.0 1))) (str.retainLl (str.tail x (float.+ 2.0 (float.shl10 -1.0 1))))))
