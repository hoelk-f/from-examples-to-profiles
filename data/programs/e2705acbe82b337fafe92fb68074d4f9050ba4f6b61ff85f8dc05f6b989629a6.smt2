(define-fun f ((x String)) String (str.++ (str.substr x 4 (- (str.indexof x " " 4) 4)) (str.substr x (str.indexof x "Quo2" 0) 4)))
