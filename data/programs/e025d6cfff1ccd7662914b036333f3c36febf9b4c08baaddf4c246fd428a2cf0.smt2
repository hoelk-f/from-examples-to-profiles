(define-fun f ((x String)) String (str.tail x (int.+ 4 (int.neg (list.len (str.retainLl x))))))
