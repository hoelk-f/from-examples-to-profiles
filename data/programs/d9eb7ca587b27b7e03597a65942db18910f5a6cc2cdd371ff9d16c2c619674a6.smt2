(define-fun f ((x String)) String (str.substr (str.++ "03:00 AM -> 11:00 AM" x) (str.len x) (str.len "01:00 PM -> 05:00 PM")))
