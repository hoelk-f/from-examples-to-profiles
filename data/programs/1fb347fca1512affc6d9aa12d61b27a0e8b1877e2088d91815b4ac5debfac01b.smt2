(define-fun f ((x String)) String (str.substr (str.substr x 5 (str.len "Renault")) 0 (+ (str.indexof x "Renault" 0) 5)))
