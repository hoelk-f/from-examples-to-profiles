(define-fun f ((x String)) String (str.++ (str.substr x (+ 5 1) (str.len "placeat")) (str.at "delectus" (str.indexof (str.++ " " x) "delectus" 0))))
