(define-fun f ((x String)) String (str.++ (int.fmt #width:0 (date.year (date.parse (list.at (str.split x e" ") 0.0)))) (list.at (str.split e" " e" ") -1.0)))
