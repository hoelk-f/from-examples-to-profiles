(define-fun f ((x String)) String (str.++ (month.fmt #abbv:false (date.month (date.parse x))) (list.at (str.split e" " e" ") 0)))
