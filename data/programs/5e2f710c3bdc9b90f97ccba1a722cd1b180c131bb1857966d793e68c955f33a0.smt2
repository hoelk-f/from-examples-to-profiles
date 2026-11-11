(define-fun f ((x String)) String (str.++ (str.substr "Glasgow" 0 (str.indexof x "5 " 0)) (str.substr "Leeds" (str.indexof x "5 " 0) 5)))
