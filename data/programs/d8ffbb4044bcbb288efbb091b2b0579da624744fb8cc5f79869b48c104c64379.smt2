(define-fun f ((x String)) String (str.substr (str.replace x " " ".tex") (str.len (str.++ "04-imp.tex" "04-imp.tex")) (str.len "04-imp.tex")))
