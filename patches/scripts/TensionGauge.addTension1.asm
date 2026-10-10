; target: TensionGauge addTension argc=1 table=methods
; original-sha1: 207c3fe90c83d25daedf483b049557f39768de73
; reason: No Losses: the conversation gauge keeps its tension too (it is what the walk-home and kiss checks read).
; Easy mode (D-038): the lines up to `orig:` are new; from `orig:` on it is the original method
; (22 bytes, listed with tools/reinsert/scfasm.py listing()). With the flag off it runs unchanged.
push_nils 0
push_temp 0
push_int 0
op <
jump_if_false orig
push_const class:GameParam
push_int 1
send 1 #easy                ; easy mode "No Losses" on?
jump_if_false orig
return_self
orig:
push_classvar.b idx:2 7
push_temp 0
send.b 1 idx:20
pop
push_temp 0
store_classvar.b idx:2 9
push_int 2
store_classvar.b idx:2 13
return_self
