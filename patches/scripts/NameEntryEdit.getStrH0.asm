; target: NameEntryEdit getStrH argc=0 table=methods
; original-sha1: 1935fcbd9dec65bcc19c009740e787c08f168f4a (115 bytes)
; reason: surname = slots 0..7 through getStr: 0 to: fieldN (was 3 slots); empty restores the current surname.
push_nils 1
push_self
push_int 0
push_self
send 0 #fieldN
send 2 #getStr
store_temp 0
push_temp 0
send 0 #length
push_int 0
identical
jump_if_false Lend15
push_const class:GameParam
send 0 #getMyouji
store_temp 0
Lend15:
push_temp 0
return_top
return_self
