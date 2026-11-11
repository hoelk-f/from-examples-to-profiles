(define-fun f ((x String)) String (str.substr (str.++ " " (str.replace x ")" "")) (str.indexof (str.++ "son" x) " " 0) (- (str.len x) (str.len "daughter"))))
