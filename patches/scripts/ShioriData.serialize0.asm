; target: ShioriData serialize argc=0 table=methods
; original-sha1: b1a2c611440d5d520942b69a0fa631e97515e909 (112 bytes)
; reason: the slot header is 256 bytes and anything longer is cut by the native writer, which makes the header unreadable and
; blanks all 20 slots on the next load. With names of up to 8 + 8 characters the header can exceed 256 bytes
; (216 bytes of fixed content in the best case, 248 with two bad-date entries per girl, plus 2 bytes per name
; character), so: serialize, and while the result is longer than 256 bytes drop the last character of the longer name
; (this copy only; the game keeps the full names). D-016.
push_nils 7
push_const class:Array
push_ivar 4
send 0 #length
send 1 #new
store_temp 1
push_int 0
store_temp 2
Lwh3:
push_temp 2
push_ivar 4
send 0 #length
push_int 1
op -
op <=
jump_if_false Lend3
push_temp 1
push_temp 2
push_ivar 4
push_temp 2
at
send 0 #makeArray
at_put
pop
push_temp 2
push_int 1
op +
store_temp 2
jump Lwh3
Lend3:
push_ivar 1
store_temp 3
push_ivar 2
store_temp 4
push_true
store_temp 6
Lwh4:
push_temp 6
jump_if_false Lend4
push_const class:Array
push_int 5
send 1 #new
store_temp 0
push_temp 0
push_int 0
push_ivar 0
at_put
pop
push_temp 0
push_int 1
push_temp 3
at_put
pop
push_temp 0
push_int 2
push_temp 4
at_put
pop
push_temp 0
push_int 3
push_ivar 3
at_put
pop
push_temp 0
push_int 4
push_temp 1
at_put
pop
push_self
push_temp 0
send 1 #serialize
store_temp 5
push_temp 5
send 0 #length
push_const int:0x100
op <=
jump_if_false Lelse5
push_false
store_temp 6
jump Lend5
Lelse5:
push_temp 3
send 0 #length
push_temp 4
send 0 #length
op >=
jump_if_false Lelse6
push_temp 3
send 0 #length
push_int 0
op >
jump_if_false Lelse7
push_self
push_temp 3
send 1 #cut
store_temp 3
jump Lend7
Lelse7:
push_false
store_temp 6
Lend7:
jump Lend6
Lelse6:
push_self
push_temp 4
send 1 #cut
store_temp 4
Lend6:
Lend5:
jump Lwh4
Lend4:
push_temp 5
return_top
return_self
