(define-fun f ((x String)) String (list.at (str.split (str.tail x 5) (list.at (str.split x e"") 4)) (str.to.int (list.at (str.split (int.to.str (list.len x)) e"") (int.neg 3)))))
