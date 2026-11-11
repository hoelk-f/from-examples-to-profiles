(define-fun f ((x String)) String (str.++ (str.substr x 5 5) (str.at "25 Apr" (str.indexof x "25 Apr" 0))))
