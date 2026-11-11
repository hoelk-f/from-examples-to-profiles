(define-fun f ((x String)) String (str.++ (str.substr x 1 2) (str.replace (str.at x 3) " " "")))
