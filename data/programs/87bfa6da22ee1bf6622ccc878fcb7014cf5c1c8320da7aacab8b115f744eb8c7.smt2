(define-fun f ((x String)) String (str.++ (int.fmt #width:2 (date.day (date.parse (str.head x (float.+ 5.0 5.0))))) (list.at (str.split e" " e" ") -1.0)))
