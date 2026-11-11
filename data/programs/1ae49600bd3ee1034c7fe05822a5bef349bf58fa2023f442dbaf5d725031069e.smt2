(define-fun f ((x String)) String (str.substr (str.replace x " followers " "") (str.indexof x " followers " 0) (str.len "522 following")))
