(define-fun f ((x String)) String (str.substr (str.replace x "s/" "") (str.indexof x "s/" (str.len "pdf.pdf")) (str.len "talk.ppt")))
