; add: GameParam setEasyFlags argc=1 table=methods2
; reason: Easy mode (D-038): stores the switch bits in class variable 18 (see easyFlags).
push_nils 0
push_temp 0
store_ivar 18
return_self
