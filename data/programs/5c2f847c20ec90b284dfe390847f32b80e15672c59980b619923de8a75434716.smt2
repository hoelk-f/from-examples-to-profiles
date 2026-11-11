(define-fun f ((x String)) String (str.substr (str.++ x x) 0 (str.indexof x "\u{5c}" 0)))
