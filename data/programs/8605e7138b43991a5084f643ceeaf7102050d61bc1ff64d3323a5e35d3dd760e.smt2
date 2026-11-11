(define-fun f ((x String)) String (str.substr (str.substr x 0 5) 0 (- (str.len x) 3)))
