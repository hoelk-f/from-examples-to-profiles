(define-fun f ((x String)) String (str.++ (str.++ (list.at (str.split x e" ") 1) e" ") (str.++ (month.fmt #abbv:true (int.+ -1 (int.+ 4 (int.+ 4 4)))) (str.++ e" " (list.at (str.split x e" ") 3)))))
