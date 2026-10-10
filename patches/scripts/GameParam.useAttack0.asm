; target: GameParam useAttack argc=0 table=methods
; original-sha1: 6d2326a870a1e324f4dacd4b20c76a16c0b775a4
; reason: More Tries: inviting her home or going for a kiss does not use up the day's Attack.
; Easy mode (D-038): the lines up to `orig:` are new; from `orig:` on it is the original method
; (22 bytes, listed with tools/reinsert/scfasm.py listing()). With the flag off it runs unchanged.
push_nils 0
push_const class:GameParam
push_int 8
send 1 #easy                ; easy mode "More Tries" on?
jump_if_false orig
push_true
return_top
orig:
push_ivar 16
push_int 0
op >
jump_if_false.l L0013
push_ivar 16
push_int 1
op -
store_ivar 16
push_true
return_top
L0013: push_false
return_top
return_self
