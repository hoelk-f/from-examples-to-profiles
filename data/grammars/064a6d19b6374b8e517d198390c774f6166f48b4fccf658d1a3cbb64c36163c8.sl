(set-logic SLIA)
(synth-fun f ((x String)) String ((S String (x "" "." "/" "//www.stanford.edu/news/" "/news/" ":" "://" "://www.stanford.edu/news" "http://www.stanford.edu/" "p://www.stanford.edu/new" "tp://www.stanford.edu/ne" "ttp://www.stanford.edu/n" (str.++ S S) (str.at S I) (str.substr S I I) (str.replace S S S) (ite B S S))) (I Int (-1 0 1 2 3 4 5 (str.len S) (str.indexof S S I) (+ I I) (- I I))) (B Bool ((str.contains S S) (str.prefixof S S) (str.suffixof S S) (= S S) (= I I)))))
(constraint (= (f "http://www.stanford.edu/news/") "/news/"))
(check-synth)
