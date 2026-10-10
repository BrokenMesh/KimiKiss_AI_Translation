; target: Favor addInterest argc=1 table=methods
; original-sha1: 6da1038c5dd4240e87d42f5385a4c561390917ba
; reason: No Losses: interest is never lowered (declining her, jealousy); raising it works as before.
; Easy mode (D-038): the lines up to `orig:` are new; from `orig:` on it is the original method
; (71 bytes, listed with tools/reinsert/scfasm.py listing()). With the flag off it runs unchanged.
push_nils 0
push_temp 0
push_int 0
op <
jump_if_false orig
push_const class:GameParam
push_int 1
send 1 #easy                ; easy mode "No Losses" on?
jump_if_false orig
push_ivar 11                ; interest, unchanged
return_top
orig:
push_temp 0
push_int 0
op >
jump_if_false.l L001a
push_self
push_temp 0
push_int 8
op *
send.b 1 idx:36
pop
push_true
store_ivar 12
jump.l L0024
L001a: push_self
push_temp 0
push_int 24
op *
send.b 1 idx:36
pop
L0024: push_ivar 11
push_temp 0
op +
store_ivar 11
push_ivar 11
push_int 0
op <
jump_if_false.l L0037
push_int 0
store_ivar 11
L0037: push_ivar 11
push_int 9
op >
jump_if_false.l L0043
push_int 9
store_ivar 11
L0043: push_ivar 11
return_top
return_self
