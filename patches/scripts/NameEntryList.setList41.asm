; target: NameEntryList setList4 argc=1 table=methods
; original-sha1: d77033e8a9e1844445cc13c829776327b0711c9f (225 bytes)
; reason: history page (names of the save slots): the four columns move to x -124, -28, 68, 164 (was -100, -16, 80, 164),
; a pitch of 96 px, so English names of up to 8 letters fit a column. D-016.
push_nils 1
push_int 0
store_temp 1
L0006: push_temp 1
push_temp 0
op <=
jump_if_false L00e0
push_ivar 1
push_temp 1
at
push_int 0
at
push_const float:-124.0
push_const.b idx:40
push_temp 1
push_int 28
op *
op +
send.b 2 idx:6
pop
push_ivar 1
push_temp 1
at
push_int 0
at
push_const.b idx:13
send.b 1 idx:18
push_ivar 8
push_ivar 9
push_temp 1
op +
at
push_int 0
at
send.b 1 idx:39
pop
push_ivar 1
push_temp 1
at
push_int 1
at
push_const float:-28.0
push_const.b idx:40
push_temp 1
push_int 28
op *
op +
send.b 2 idx:6
pop
push_ivar 1
push_temp 1
at
push_int 1
at
push_const.b idx:13
send.b 1 idx:18
push_ivar 8
push_ivar 9
push_temp 1
op +
at
push_int 1
at
send.b 1 idx:39
pop
push_ivar 1
push_temp 1
at
push_int 2
at
push_const float:68.0
push_const.b idx:40
push_temp 1
push_int 28
op *
op +
send.b 2 idx:6
pop
push_ivar 1
push_temp 1
at
push_int 2
at
push_const.b idx:13
send.b 1 idx:18
push_ivar 8
push_ivar 9
push_temp 1
op +
at
push_int 2
at
send.b 1 idx:39
pop
push_ivar 1
push_temp 1
at
push_int 3
at
push_const float:164.0
push_const.b idx:40
push_temp 1
push_int 28
op *
op +
send.b 2 idx:6
pop
push_ivar 1
push_temp 1
at
push_int 3
at
push_const.b idx:13
send.b 1 idx:18
push_ivar 8
push_ivar 9
push_temp 1
op +
at
push_int 3
at
send.b 1 idx:39
pop
push_temp 1
push_int 1
op +
store_temp 1
jump L0006
L00e0: return_self
