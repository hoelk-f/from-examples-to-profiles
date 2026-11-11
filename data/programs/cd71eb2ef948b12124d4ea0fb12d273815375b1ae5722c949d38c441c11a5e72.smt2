(define-fun f ((x String)) String (str.++ (list.at (str.split x (list.at (str.split x (str.retainN x)) 5)) -1) (list.at (str.split x (str.head x (int.+ 2 5))) (str.count x (int.to.str 2)))))
