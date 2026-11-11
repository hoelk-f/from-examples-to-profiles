(define-fun f ((x String)) String (list.at (str.split x (list.at (str.split x e"") 2)) (str.count (str.retainLc x) e"")))
