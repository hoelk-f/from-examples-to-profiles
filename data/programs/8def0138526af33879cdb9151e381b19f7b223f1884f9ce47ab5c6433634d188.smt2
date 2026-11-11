(define-fun f ((x String)) String (str.++ (float.fmt #left:0 #right:2 (float.shl10 (str.to.float (str.retainN x)) (int.neg 2))) (list.at (str.split e" " e" ") -1.0)))
