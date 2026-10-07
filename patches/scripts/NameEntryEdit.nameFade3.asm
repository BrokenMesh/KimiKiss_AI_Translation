; target: NameEntryEdit nameFade argc=3 table=methods
; original-sha1: 89e7a280c42f7f536d9817e456a6b39cf621ab37 (54 bytes)
; reason: loop over all slots (self slots) instead of the fixed 6 (0..5).
push_nils 1
push_int 0
store_temp 3
Lwh17:
push_temp 3
push_self
send 0 #slots
op <
jump_if_false Lend17
push_ivar 13
push_temp 3
at
push_temp 0
push_temp 1
push_temp 2
send 3 #fade
pop
push_ivar 2
push_temp 3
at
push_temp 0
push_temp 1
push_temp 2
send 3 #fade
pop
push_temp 3
push_int 1
op +
store_temp 3
jump Lwh17
Lend17:
return_self
