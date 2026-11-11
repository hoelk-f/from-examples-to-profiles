(define-fun f ((x String)) String (str.++ (str.substr x 2 (str.len "Harold Macmillan")) (str.at "Harold Macmillan" (str.indexof x "Margaret Thatcher" 0))))
