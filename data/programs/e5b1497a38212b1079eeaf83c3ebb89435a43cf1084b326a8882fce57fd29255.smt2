(define-fun f ((x String)) String (str.substr (str.replace x ".h>" "") (str.len "#include <") (str.len "malloc")))
