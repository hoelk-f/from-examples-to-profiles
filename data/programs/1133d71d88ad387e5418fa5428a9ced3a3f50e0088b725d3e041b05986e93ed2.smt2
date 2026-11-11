(define-fun f ((x String)) String (str.substr (str.replace (str.++ x "1870") "1870" "") (- (str.len x) 4) 4))
