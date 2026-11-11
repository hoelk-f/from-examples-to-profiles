(define-fun f ((x String)) String (list.at (str.split (list.at (str.split x (list.at (str.split x e"") 1)) 1) (str.tail x -1)) 1))
