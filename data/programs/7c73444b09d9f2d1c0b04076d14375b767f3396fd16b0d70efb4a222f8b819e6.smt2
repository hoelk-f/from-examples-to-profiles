(define-fun f ((x String)) String (str.substr (str.replace (str.++ "** [[Meena Kumari]] \u{2013} ''" "Azaad") " " "Sahara") (+ (str.indexof x "Azaad" 0) 3) (str.len "Sahara")))
