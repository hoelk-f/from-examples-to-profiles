(set-logic SLIA)
(synth-fun f ((x String)) String ((S String (x "" " " " opt is the root of evil" "ature opt is the root of" "e opt is the root of evi" "emature opt is the root " "evil" "mature opt is the root o" "premature opt is the roo" "re opt is the root of ev" "remature opt is the root" "ture opt is the root of " "ure opt is the root of e" (str.++ S S) (str.at S I) (str.substr S I I) (str.replace S S S) (ite B S S))) (I Int (-1 0 1 2 3 4 5 (str.len S) (str.indexof S S I) (+ I I) (- I I))) (B Bool ((str.contains S S) (str.prefixof S S) (str.suffixof S S) (= S S) (= I I)))))
(constraint (= (f "premature opt is the root of evil") "evil"))
(check-synth)
