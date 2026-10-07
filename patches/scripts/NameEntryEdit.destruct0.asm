; target: NameEntryEdit destruct argc=0 table=methods
; original-sha1: 1c96a1ccef1d08e291ea96b208a0175e557d0adb (119 bytes)
; reason: loop over all slots (self slots) instead of the fixed 6 (0..5); the rest is the original.
push_nils 1
push_ivar 17
push_nil
not_identical
jump_if_false L0012
push_ivar 17
send.b 0 idx:40
pop
push_nil
store_ivar 17
L0012: push_ivar 1
send.b 0 idx:41
pop
push_ivar 3
send.b 0 idx:41
pop
push_ivar 4
send.b 0 idx:41
pop
push_ivar 5
send.b 0 idx:41
pop
push_ivar 6
send.b 0 idx:41
pop
push_ivar 7
send.b 0 idx:41
pop
push_ivar 8
send.b 0 idx:41
pop
push_ivar 9
send.b 0 idx:41
pop
push_ivar 10
push_nil
not_identical
jump_if_false L004f
push_ivar 10
send.b 0 idx:41
pop
L004f: push_int 0
store_temp 0
Lwh18:
push_temp 0
push_self
send 0 #slots
op <
jump_if_false Lend18
push_ivar 13
push_temp 0
at
send 0 #destruct
pop
push_ivar 2
push_temp 0
at
send 0 #destruct
pop
push_temp 0
push_int 1
op +
store_temp 0
jump Lwh18
Lend18:
return_self
