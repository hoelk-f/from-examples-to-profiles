(define-fun f ((x String)) String (str.substr (str.++ (str.++ "Cambridge" ", MA 021") "Dorchester") (+ (str.indexof x "#" 0) 1) (str.indexof x " St. " 0)))
