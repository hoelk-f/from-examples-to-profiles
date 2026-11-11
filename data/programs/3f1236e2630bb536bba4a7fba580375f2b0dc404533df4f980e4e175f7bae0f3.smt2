(define-fun f ((x String)) String (str.substr (str.replace (str.substr (str.++ x x) 4 (- (str.indexof x " - " 0) 4)) " " "") 0 (str.len (str.substr (str.++ x x) 4 (- (str.indexof x " - " 0) 4)))))
