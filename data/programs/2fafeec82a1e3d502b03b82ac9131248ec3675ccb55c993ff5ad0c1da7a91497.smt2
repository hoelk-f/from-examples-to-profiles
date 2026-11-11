(define-fun f ((x String)) String (str.++ (str.substr x (str.indexof x "/" (+ 5 3)) (str.len x)) ""))
