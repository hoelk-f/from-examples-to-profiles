(define-fun f ((x String)) String (str.tail (str.join (str.split x (list.at (str.split x e"") 5)) e"") 5))
