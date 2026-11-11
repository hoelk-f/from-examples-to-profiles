(define-fun f ((x String)) String (str.substr (str.replace x "USD" "YEN") (- (str.len x) 4) 3))
