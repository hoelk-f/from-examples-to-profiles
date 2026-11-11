(define-fun f ((x String)) String (str.++ (month.fmt #abbv:false (date.month (date.parse (list.at (str.split x e" ") 1.0)))) (list.at (str.split e" " e" ") -1.0)))
