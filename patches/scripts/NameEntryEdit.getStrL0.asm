; target: NameEntryEdit getStrL argc=0 table=methods
; original-sha1: 697c93d507fa18f4cf775ebf930124fb27a23377 (115 bytes)
; reason: given name = slots 8..15 through getStr:to: (was 3 slots); empty restores the current given name.
push_nils 1
push_self
push_self
send 0 #fieldN
push_self
send 0 #slots
send 2 #getStr
store_temp 0
push_temp 0
send 0 #length
push_int 0
identical
jump_if_false Lend16
push_const class:GameParam
send 0 #getNamae
store_temp 0
Lend16:
push_temp 0
return_top
return_self
