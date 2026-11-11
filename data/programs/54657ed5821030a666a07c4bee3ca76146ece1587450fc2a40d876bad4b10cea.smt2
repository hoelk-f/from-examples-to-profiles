(define-fun f ((x String)) String (str.++ (str.head (str.tail x (int.+ 5 5)) 5) (list.at (str.split x (list.at (str.split x (list.at (str.split x e"") 5)) 2)) 4)))
