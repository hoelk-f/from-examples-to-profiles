(define-fun f ((x String)) String (str.substr (str.replace x "3,000</strong>" "3,000") (str.len "<strong>&pound;") (str.len "633,000")))
