(define-fun f ((x String)) String (str.substr (str.++ " " x) (- (str.len x) 2) 3))
