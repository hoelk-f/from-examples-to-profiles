(define-fun f ((x String)) String (str.substr (str.replace x "Dec 2, 2014, 11=2" "") (str.len (str.++ " PM - +91 90000 80000= " " ")) (str.len x)))
