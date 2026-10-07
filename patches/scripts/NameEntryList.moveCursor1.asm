; target: NameEntryList moveCursor argc=1 table=methods
; original-sha1: a9a51389f27a1a9bf58ae4973c6e3971d2d60f9c (328 bytes)
; reason: history page cursor: centres -88, 8, 104, 200 (-88 + 96 curX) and a 96 px wide highlight (zoom 3.84, was 3), to
; match the wider columns of setList4. D-016.
push_nils 1
push_ivar 8
push_ivar 9
push_ivar 5
op +
at
send.b 0 idx:32
store_temp 1
push_ivar 12
push_true
identical
jump_if_false L0047
push_ivar 3
push_const.b idx:10
push_int 12
push_int 16
push_temp 1
op -
push_ivar 4
push_int 2
op *
op +
op *
op +
push_const.b idx:43
push_ivar 5
push_int 28
op *
op +
push_int 1
push_temp 0
send.b 4 idx:56
push_const.b idx:13
push_const.b idx:13
push_int 1
push_temp 0
send.b 4 idx:57
pop
jump L0147
L0047: push_ivar 10
push_int 0
identical
push_ivar 10
push_int 3
identical
or
jump_if_false L0086
push_ivar 3
push_const.b idx:10
push_int 12
push_int 16
push_temp 1
op -
push_ivar 4
push_int 2
op *
op +
op *
op +
push_const.b idx:40
push_ivar 5
push_int 28
op *
op +
push_int 1
push_temp 0
send.b 4 idx:56
push_const.b idx:13
push_const.b idx:13
push_int 1
push_temp 0
send.b 4 idx:57
pop
jump L0147
L0086: push_ivar 10
push_int 4
identical
jump_if_false L00b3
push_ivar 3
push_const float:-88.0
push_const float:96.0
push_ivar 4
op *
op +
push_const.b idx:40
push_ivar 5
push_int 28
op *
op +
push_int 1
push_temp 0
send.b 4 idx:56
push_const float:3.84
push_const.b idx:13
push_int 1
push_temp 0
send.b 4 idx:57
pop
jump L0147
L00b3: push_ivar 10
push_int 5
identical
jump_if_false L00e0
push_ivar 3
push_const.b idx:59
push_ivar 4
at
push_const.b idx:40
push_ivar 5
push_int 28
op *
op +
push_int 1
push_temp 0
send.b 4 idx:56
push_const.b idx:60
push_const.b idx:13
push_int 1
push_temp 0
send.b 4 idx:57
pop
jump L0147
L00e0: push_ivar 5
push_int 5
op <
jump_if_false L0119
push_ivar 3
push_const.b idx:10
push_int 12
push_int 16
push_temp 1
op -
push_ivar 4
push_int 2
op *
op +
op *
op +
push_const.b idx:40
push_ivar 5
push_int 28
op *
op +
push_int 1
push_temp 0
send.b 4 idx:56
push_const.b idx:13
push_const.b idx:13
push_int 1
push_temp 0
send.b 4 idx:57
pop
jump L0147
L0119: push_ivar 3
push_const.b idx:10
push_int 12
push_int 16
push_temp 1
op -
push_ivar 4
push_int 2
op *
op +
op *
op +
push_const.b idx:41
push_ivar 5
push_int 28
op *
op +
push_int 1
push_temp 0
send.b 4 idx:56
push_const.b idx:13
push_const.b idx:13
push_int 1
push_temp 0
send.b 4 idx:57
pop
L0147: return_self
