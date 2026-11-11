(define-fun f ((x String)) String (str.substr (str.++ "07:00 AM -> 10:00 AM" x) (str.len x) (str.len "01:00 PM -> 05:00 PM")))
