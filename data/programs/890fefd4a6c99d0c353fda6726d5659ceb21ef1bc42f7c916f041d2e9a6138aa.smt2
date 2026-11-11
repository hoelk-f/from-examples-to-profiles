(define-fun f ((x String)) String (str.tail (str.head x (list.len (str.retainL x))) 2))
