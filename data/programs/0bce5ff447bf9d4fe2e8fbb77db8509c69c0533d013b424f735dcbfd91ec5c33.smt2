(define-fun f ((x String)) String (str.substr (str.++ "Cory" "Massachusetts") (+ (str.indexof x "Massachusetts" 0) 1) (str.indexof (str.++ " " x) " " 4)))
