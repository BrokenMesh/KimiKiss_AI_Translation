; add: GameParam easy argc=1 table=methods2
; reason: Easy mode (D-038): `GameParam easy: bit` -> true when that switch is on (see easyFlags).
push_nils 0
push_self
send 0 #easyFlags
push_temp 0
op &
push_int 0
op <>
return_top
return_self
