(define-fun f ((x String)) String (str.substr (str.replace x "db" ".") (- (str.len x) 3) 3))
