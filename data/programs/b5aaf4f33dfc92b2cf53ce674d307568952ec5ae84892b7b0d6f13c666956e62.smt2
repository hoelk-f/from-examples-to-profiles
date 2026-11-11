(define-fun f ((x String)) String (str.substr (str.replace x " OS " "-internal ") (str.len (str.++ " " x)) 5))
