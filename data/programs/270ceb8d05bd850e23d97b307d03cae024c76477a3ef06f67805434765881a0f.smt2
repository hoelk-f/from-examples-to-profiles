(define-fun f ((x String)) String (str.substr (str.replace x ", " "") (str.indexof x ", September 1" 0) (str.len "September 10-12, 2008")))
