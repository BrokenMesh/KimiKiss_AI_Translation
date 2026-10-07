; target: Parson setDispName argc=1 table=methods
; original-sha1: 7d5b3ccb241c51054c72def2de766f2504ce8fb3 (142 bytes)
; reason: the name plate is the whole surname (was: padded to 3 cells for 1 and 2 characters, cut at 3). An empty surname
; still gives the blank 3-cell plate. D-016.
push_nils 0
push_temp 0
push_nil
not_identical
push_temp 0
push_const class:String
send 1 #isKindOf
and
jump_if_false Lend0
push_temp 0
send 0 #length
push_int 0
identical
jump_if_false Lelse1
push_const "　　　"
store_ivar 13
jump Lend1
Lelse1:
push_temp 0
store_ivar 13
Lend1:
Lend0:
return_self
