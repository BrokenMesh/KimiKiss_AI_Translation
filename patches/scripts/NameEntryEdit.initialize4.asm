; target: NameEntryEdit initialize argc=4 table=methods
; original-sha1: 36d7521c7f05730b2aefed4bd960d261c34e5067 (101 bytes)
; reason: pad surname and given name to 8 characters with the full-width blank (was 3).
push_nils 0
Lwh39:
push_temp 2
send 0 #length
push_int 8
op <
jump_if_false Lend39
push_temp 2
push_const "　"
op +
store_temp 2
jump Lwh39
Lend39:
Lwh40:
push_temp 3
send 0 #length
push_int 8
op <
jump_if_false Lend40
push_temp 3
push_const "　"
op +
store_temp 3
jump Lwh40
Lend40:
push_self
push_temp 0
push_temp 1
push_temp 2
push_temp 3
op +
send 3 #initialize
pop
return_self
