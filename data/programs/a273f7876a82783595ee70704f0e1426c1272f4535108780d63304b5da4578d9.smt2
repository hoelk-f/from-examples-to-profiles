(define-fun f ((x String)) String (str.substr (str.substr x 4 (+ 5 5)) (- (str.indexof x "." 0) 3) (+ (str.indexof x "." 0) -1)))
