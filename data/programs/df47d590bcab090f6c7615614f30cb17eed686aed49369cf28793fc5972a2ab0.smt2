(define-fun f ((x String)) String (str.++ (int.fmt #width:0 (date.year (date.parse x))) (list.at (str.split e" " e" ") 0)))
