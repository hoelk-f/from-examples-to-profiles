(define-fun f ((x String)) String (str.substr (str.++ (str.++ "gov" "gov") "example") (- 5 (str.indexof x "gov" 0)) (+ (str.indexof x "." 4) -1)))
