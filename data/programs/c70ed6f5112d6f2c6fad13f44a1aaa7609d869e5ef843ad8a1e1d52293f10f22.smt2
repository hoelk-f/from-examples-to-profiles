(define-fun f ((x String)) String (str.substr (str.++ " (" x) (str.indexof x ":" 0) (str.len "10:00 PM -> 05:00 PM (+1 day)")))
