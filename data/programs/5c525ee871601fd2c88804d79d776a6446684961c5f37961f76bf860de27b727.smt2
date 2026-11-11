(define-fun f ((x String)) String (str.substr (str.replace x "</country>" "") (str.len "<country>") (str.len "Scotland")))
