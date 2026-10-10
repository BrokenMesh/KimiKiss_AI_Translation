; target: Favor addTension argc=1 table=methods
; original-sha1: 69463fbb06add445050aa805b6c802ae9bec7874
; reason: No Losses: a negative tension change (bad reaction, end-of-talk settlement) is dropped.
; Easy mode (D-038): the lines up to `orig:` are new; from `orig:` on it is the original method
; (16 bytes, listed with tools/reinsert/scfasm.py listing()). With the flag off it runs unchanged.
push_nils 0
push_temp 0
push_int 0
op <
jump_if_false orig
push_const class:GameParam
push_int 1
send 1 #easy                ; easy mode "No Losses" on?
jump_if_false orig
push_ivar 17                ; tension, unchanged
return_top
orig:
push_self
push_ivar 17
push_temp 0
op +
send.b 1 idx:34
pop
push_ivar 17
return_top
return_self
