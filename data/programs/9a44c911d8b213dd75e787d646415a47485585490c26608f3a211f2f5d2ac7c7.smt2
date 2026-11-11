(define-fun f ((x String)) String (str.substr (str.replace x "08" "49") (- (str.len x) 2) 2))
