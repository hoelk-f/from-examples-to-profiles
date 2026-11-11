(define-fun f ((x String)) String (str.++ (str.substr "1964, 1987, 1990, 1995" 0 (str.indexof x "1964, 1987, 1990, 1995" 0)) (str.substr "1956, 1975, 1981" 0 (str.indexof x "1956, 1975, 1981" 0))))
