(define-fun f ((x String)) String (str.substr (str.++ ", " (str.replace x ", MasterCard" "")) (str.indexof (str.++ ", MasterCard" x) "/" 0) (str.len "Holli Claxton")))
