; target: Favor addBad argc=1 table=methods
; original-sha1: 202c1113f53cac3ce9ea6dd701f7035810d8d5fe
; reason: No Losses: no jealousy mark, so a girl never drops out of the game after two.
; Easy mode (D-038): the lines up to `orig:` are new; from `orig:` on it is the original method
; (35 bytes, listed with tools/reinsert/scfasm.py listing()). With the flag off it runs unchanged.
push_nils 0
push_const class:GameParam
push_int 1
send 1 #easy                ; easy mode "No Losses" on?
jump_if_false orig
push_ivar 6                 ; bad, unchanged
return_top
orig:
push_ivar 6
push_int 0
at
push_nil
not_identical
jump_if_false.l L0017
push_ivar 6
push_int 1
push_ivar 6
push_int 0
at
at_put
pop
L0017: push_ivar 6
push_int 0
push_temp 0
at_put
pop
push_ivar 6
return_top
return_self
