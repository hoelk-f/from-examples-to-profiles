(define-fun f ((x String)) String (str.++ (str.substr x (str.indexof x "/news/" 0) 5) (str.replace (str.at x 5) ":" "/stuff/")))
