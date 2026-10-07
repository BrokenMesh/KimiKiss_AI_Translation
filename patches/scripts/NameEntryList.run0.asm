; target: NameEntryList run argc=0 table=methods
; original-sha1: b107d492445b0217e68a244d76221d02b25d4eb4 (170 bytes)
; reason: the first page is 英数記号 (page 3) instead of the kanji page 0. D-016.
push_nils 0
L0002: push_true
jump_if_false L00a9
L0006: push_ivar 15
push_int 0
identical
jump_if_false L0017
push_self
push_int 1
send.b 1 idx:80
pop
jump L0006
L0017: push_ivar 15
store_ivar 14
push_int 0
store_ivar 15
push_ivar 14
push_int 1
identical
jump_if_false L0065
push_self
send.b 0 idx:35
pop
push_ivar 0
push_const.b idx:4
push_int 40
push_int 1
push_const.b idx:81
send.b 4 idx:56
pop
push_self
push_int 12
send.b 1 idx:82
push_false
identical
jump_if_false L0047
jump L0002
L0047: push_self
push_int 3
send.b 1 idx:76
pop
push_self
push_const.b idx:34
send.b 1 idx:83
pop
push_self
push_int 3
send.b 1 idx:82
push_false
identical
jump_if_false L0062
jump L0002
L0062: jump L00a2
L0065: push_ivar 14
push_int 2
identical
jump_if_false L00a2
push_self
push_const.b idx:34
send.b 1 idx:84
pop
push_self
push_int 3
send.b 1 idx:82
push_false
identical
jump_if_false L0081
jump L0002
L0081: push_ivar 0
push_const.b idx:4
push_const.b idx:5
push_int 2
push_const.b idx:81
send.b 4 idx:56
pop
push_self
push_int 12
send.b 1 idx:82
push_false
identical
jump_if_false L009d
jump L0002
L009d: push_self
send.b 0 idx:36
pop
L00a2: push_int 0
store_ivar 14
jump L0002
L00a9: return_self
