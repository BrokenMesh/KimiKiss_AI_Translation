; target: Favor downFeel argc=0 table=methods
; original-sha1: 80f7ea5e1a48b7e4c9737e7e04617a4e0f74584b
; reason: No Losses: no note is taken off the gauge; -1 tells FavorGauge>>run there is no icon to remove.
; Easy mode (D-038): the lines up to `orig:` are new; from `orig:` on it is the original method
; (69 bytes, listed with tools/reinsert/scfasm.py listing()). With the flag off it runs unchanged.
push_nils 1
push_const class:GameParam
push_int 1
send 1 #easy                ; easy mode "No Losses" on?
jump_if_false orig
push_int -1
return_top
orig:
push_ivar 4
push_ivar 5
op +
store_temp 0
push_int 0
push_temp 0
op <
jump_if_false.l L0041
push_ivar 9
push_temp 0
push_int 1
op -
at
push_int 0
identical
jump_if_false.l L0029
push_ivar 4
push_int 1
op -
store_ivar 4
jump.l L0030
L0029: push_ivar 5
push_int 1
op -
store_ivar 5
L0030: push_ivar 9
push_temp 0
push_int 1
op -
push_nil
at_put
pop
push_temp 0
push_int 1
op -
store_temp 0
L0041: push_temp 0
return_top
return_self
