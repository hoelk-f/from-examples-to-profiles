(define-fun f ((x String)) String (str.++ (float.fmt #left:0 #right:0 (float.shl10 (str.to.float (str.retainN (list.at (str.split x e" ") -1.0))) -1)) (list.at (str.split e" " e" ") -1.0)))
