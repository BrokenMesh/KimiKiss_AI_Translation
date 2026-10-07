; add: ShioriData cut argc=1 table=methods
; reason: new method. The string without its last character (used by serialize to fit the 256-byte header). D-016.
push_nils 2
push_const ""
store_temp 1
push_int 0
store_temp 2
Lwh2:
push_temp 2
push_temp 0
send 0 #length
push_int 1
op -
op <
jump_if_false Lend2
push_temp 1
push_temp 0
push_temp 2
at
send 0 #asChar
op +
store_temp 1
push_temp 2
push_int 1
op +
store_temp 2
jump Lwh2
Lend2:
push_temp 1
return_top
return_self
