(define-fun f ((x String)) String (str.substr (str.replace x "}" "") (str.len "/section{") (str.len "Introduction")))
