; target: NameEntryEdit initialize argc=3 table=methods
; original-sha1: c4131e96daa650ecb5a37f4c78079d0b171ee7e5 (521 bytes)
; reason: arrays of self slots entries (was 6) and no const-28 position table: waku/nameChar are created at x 0 and
; placed by layout; the name is padded to slots characters. The rest (box, labels, arrows, cursor, thread) is the
; original.
push_nils 6
push_temp 0
store_ivar 12
push_temp 1
store_ivar 0
push_const.b idx:0
push_int 1
push_const.b idx:1
push_const.b idx:2
push_temp 0
send.b 4 idx:3
push_const.b idx:4
push_const.b idx:5
send.b 2 idx:6
send.b 0 idx:7
store_ivar 1
push_const.b idx:8
push_const.b idx:9
push_int 10
push_temp 0
push_int 1
op +
send.b 3 idx:3
push_const.b idx:10
push_const.b idx:5
send.b 2 idx:6
push_const.b idx:11
send.b 1 idx:12
store_ivar 3
push_const.b idx:8
push_const.b idx:13
push_int 15
push_temp 0
push_int 1
op +
send.b 3 idx:3
push_const.b idx:14
push_const.b idx:5
send.b 2 idx:6
push_const.b idx:11
send.b 1 idx:12
store_ivar 4
push_const.b idx:8
push_const.b idx:9
push_int 10
push_temp 0
push_int 1
op +
send.b 3 idx:3
push_const.b idx:15
push_ivar 0
at
push_const.b idx:5
send.b 2 idx:6
push_const.b idx:11
send.b 1 idx:12
store_ivar 5
push_const.b idx:8
push_const.b idx:9
push_int 10
push_temp 0
push_int 1
op +
send.b 3 idx:3
push_const.b idx:16
push_const.b idx:5
send.b 2 idx:6
push_const.b idx:11
send.b 1 idx:12
store_ivar 6
push_const.b idx:8
push_const.b idx:13
push_int 14
push_temp 0
push_int 1
op +
send.b 3 idx:3
push_const.b idx:17
push_const.b idx:5
send.b 2 idx:6
push_const.b idx:11
send.b 1 idx:12
store_ivar 7
push_const.b idx:8
push_int 101
push_int 0
push_temp 0
push_int 1
op +
send.b 3 idx:3
push_const.b idx:18
push_const.b idx:19
send.b 2 idx:6
push_const.b idx:11
send.b 1 idx:12
store_ivar 8
push_const.b idx:8
push_int 102
push_int 0
push_temp 0
push_int 1
op +
send.b 3 idx:3
push_const.b idx:20
push_const.b idx:19
send.b 2 idx:6
push_const.b idx:11
send.b 1 idx:12
store_ivar 9
push_int 1
store_ivar 11
push_const.b idx:8
push_int 0
push_temp 0
push_int 1
op +
send.b 2 idx:3
push_const.b idx:21
push_const.b idx:22
push_const.b idx:23
send.b 3 idx:24
push_const.b idx:11
send.b 1 idx:12
store_ivar 10
push_ivar 10
push_const.b idx:11
push_const.b idx:11
push_const.b idx:25
push_const.b idx:26
send.b 4 idx:27
pop
push_self
send 0 #slots
store_temp 5
Lwh41:
push_temp 2
send 0 #length
push_temp 5
op <
jump_if_false Lend41
push_temp 2
push_const "　"
op +
store_temp 2
jump Lwh41
Lend41:
push_const class:Array
push_temp 5
send 1 #new
store_ivar 2
push_const class:Array
push_temp 5
send 1 #new
store_ivar 14
push_const class:Array
push_temp 5
send 1 #new
store_ivar 13
push_int 0
store_temp 3
Lwh42:
push_temp 3
push_temp 5
op <
jump_if_false Lend42
push_temp 2
push_temp 3
at
store_temp 4
push_ivar 14
push_temp 3
push_temp 4
at_put
pop
push_ivar 13
push_temp 3
push_const class:FontChar
push_temp 4
push_int 3
push_temp 0
push_int 2
op +
push_const float:0.0
push_const float:-160.0
push_const float:1.0
push_const float:1.0
send 7 #new
push_const float:0.0
send 1 #setAlpha
at_put
pop
push_ivar 2
push_temp 3
push_const class:Sprite
push_const int:0x8e
push_int 0
push_temp 0
push_int 1
op +
send 3 #new
push_const float:0.0
push_const float:-144.0
send 2 #setPos
push_const float:0.0
send 1 #setAlpha
at_put
pop
push_temp 3
push_int 1
op +
store_temp 3
jump Lwh42
Lend42:
push_self
send 0 #layout
pop

push_int 0
store_ivar 15
push_int 0
store_ivar 16
push_const.b idx:36
send.b 0 idx:3
push_self
send.b 1 idx:37
store_ivar 17
return_self