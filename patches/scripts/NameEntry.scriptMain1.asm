; target: NameEntry scriptMain argc=1 table=methods
; original-sha1: c03e8cad3a71b0b392cd65088648d13dd23c0ba8 (1160 bytes)
; reason: the entry opens on the 英数記号 page (menu row 3 and curY 3 instead of 0, the kanji page), and the confirm button
; index 7 becomes `edit slots + 1`, the surname boundary 4 becomes `edit fieldN + 1` (as in selectChar). D-016.
push_nils 4
push_const.b idx:15
push_int 12
push_const.b idx:16
push_const.b idx:17
push_int 3
push_int 3
send.b 5 idx:8
store_ivar 8
push_const.b idx:15
push_int 12
push_const.b idx:18
push_const.b idx:19
push_int 0
push_int 1
send.b 5 idx:8
store_ivar 6
push_const.b idx:15
push_int 12
push_const.b idx:20
push_const.b idx:21
push_int 1
push_int 2
send.b 5 idx:8
store_ivar 7
push_temp 0
store_ivar 9
push_const.b idx:0
push_int 15
send.b 1 idx:2
pop
push_ivar 9
push_int 0
identical
jump_if_false L0064
push_const.b idx:22
push_int 10
push_int 0
push_const.b idx:23
send.b 0 idx:24
push_const.b idx:23
send.b 0 idx:25
send.b 4 idx:8
send.b 0 idx:26
store_ivar 10
jump L0077
L0064: push_const.b idx:22
push_int 10
push_int 1
push_const.b idx:27
send.b 0 idx:28
send.b 3 idx:8
send.b 0 idx:26
store_ivar 10
L0077: push_const.b idx:29
push_int 10
send.b 1 idx:8
send.b 0 idx:26
store_ivar 11
push_const.b idx:30
push_const.b idx:31
push_const.b idx:32
push_int 3
send.b 3 idx:8
send.b 0 idx:26
store_ivar 12
push_ivar 8
send.b 0 idx:26
pop
push_self
push_int 3
send.b 1 idx:10
pop
push_ivar 6
send.b 0 idx:26
pop
push_self
push_int 3
send.b 1 idx:10
pop
push_ivar 7
send.b 0 idx:26
pop
push_self
push_int 3
send.b 1 idx:10
pop
push_self
push_int 6
send.b 1 idx:10
pop
push_ivar 9
push_int 0
identical
jump_if_false L0147
push_const.b idx:23
send.b 0 idx:33
store_temp 1
push_temp 1
push_nil
identical
jump_if_false L00de
push_int 0
store_temp 1
jump L0123
L00de: push_temp 1
push_int 0
identical
jump_if_false L0116
push_const.b idx:23
send.b 0 idx:34
store_temp 1
push_temp 1
push_nil
identical
jump_if_false L00fb
push_int 0
store_temp 1
jump L0113
L00fb: push_const.b idx:35
push_temp 1
at
push_nil
identical
jump_if_false L010f
push_temp 1
push_int 1
op -
store_temp 1
jump L0113
L010f: push_int 0
store_temp 1
L0113: jump L0123
L0116: push_const.b idx:36
push_temp 1
push_int 1
op -
at
push_int 1
op -
store_temp 1
L0123: push_const.b idx:23
send.b 0 idx:37
store_temp 2
push_temp 2
push_nil
identical
jump_if_false L0135
push_int 0
store_temp 2
L0135: push_temp 1
push_int 2
op *
push_temp 2
op +
store_temp 1
push_temp 1
store_ivar 15
push_temp 1
store_ivar 16
L0147: push_int 1
store_ivar 13
push_int 3
store_ivar 14
L014f: push_temp 3
push_nil
identical
jump_if_false L03ed
push_const.b idx:11
send.b 0 idx:12
push_const.b idx:38
op &
push_int 0
not_identical
jump_if_false L01b1
push_ivar 10
push_ivar 10
send 0 #slots
push_int 1
op +
send.b 1 idx:39
pop
push_ivar 12
send.b 0 idx:40
pop
push_self
push_true
send.b 1 idx:41
push_true
identical
jump_if_false L0191
push_const.b idx:0
push_int 19
send.b 1 idx:2
pop
push_self
push_int 30
send.b 1 idx:10
pop
push_true
store_temp 3
jump L01ae
L0191: push_const.b idx:0
push_int 23
send.b 1 idx:2
pop
push_ivar 10
push_ivar 13
send.b 1 idx:39
pop
push_ivar 12
send.b 0 idx:42
pop
push_self
push_int 3
send.b 1 idx:10
pop
L01ae: jump L02f4
L01b1: push_const.b idx:11
send.b 0 idx:12
push_int 32
op &
push_int 0
not_identical
jump_if_false L01ec
push_const.b idx:0
push_int 35
send.b 1 idx:2
pop
push_ivar 12
send.b 0 idx:40
pop
push_self
push_ivar 14
send.b 1 idx:43
store_temp 3
push_temp 3
push_nil
identical
jump_if_false L01e2
push_ivar 12
send.b 0 idx:42
pop
L01e2: push_self
push_int 3
send.b 1 idx:10
pop
jump L02f4
L01ec: push_const.b idx:11
send.b 0 idx:12
push_int 64
op &
push_int 0
not_identical
jump_if_false L0240
push_ivar 10
push_int 0
send.b 1 idx:39
pop
push_ivar 12
send.b 0 idx:40
pop
push_self
push_false
send.b 1 idx:41
push_true
identical
jump_if_false L0220
push_const.b idx:0
push_int 24
send.b 1 idx:2
pop
push_false
store_temp 3
jump L023d
L0220: push_const.b idx:0
push_int 23
send.b 1 idx:2
pop
push_ivar 10
push_ivar 13
send.b 1 idx:39
pop
push_ivar 12
send.b 0 idx:42
pop
push_self
push_int 3
send.b 1 idx:10
pop
L023d: jump L02f4
L0240: push_const.b idx:11
send.b 0 idx:12
push_const.b idx:44
op &
push_int 0
not_identical
jump_if_false L0260
push_const.b idx:0
push_int 24
send.b 1 idx:2
pop
push_ivar 10
send.b 0 idx:45
store_ivar 13
jump L02f4
L0260: push_const.b idx:11
send.b 0 idx:46
push_const.b idx:47
op &
push_int 0
not_identical
jump_if_false L02b1
push_const.b idx:0
push_int 13
send.b 1 idx:2
pop
push_const.b idx:11
send.b 0 idx:46
push_const.b idx:48
op &
push_int 0
not_identical
jump_if_false L028e
push_ivar 12
send.b 0 idx:49
store_ivar 14
jump L02a3
L028e: push_const.b idx:11
send.b 0 idx:46
push_const.b idx:50
op &
push_int 0
not_identical
jump_if_false L02a3
push_ivar 12
send.b 0 idx:51
store_ivar 14
L02a3: push_ivar 11
push_const.b idx:52
push_ivar 9
at
push_ivar 14
at
send.b 1 idx:53
pop
L02b1: push_const.b idx:11
send.b 0 idx:46
push_int 15
op &
push_int 0
not_identical
jump_if_false L02f4
push_const.b idx:0
push_int 14
send.b 1 idx:2
pop
push_const.b idx:11
send.b 0 idx:46
push_int 5
op &
push_int 0
not_identical
jump_if_false L02df
push_ivar 10
send.b 0 idx:54
store_ivar 13
jump L02f4
L02df: push_const.b idx:11
send.b 0 idx:46
push_int 10
op &
push_int 0
not_identical
jump_if_false L02f4
push_ivar 10
send.b 0 idx:55
store_ivar 13
L02f4: push_temp 3
push_nil
identical
jump_if_false L03e3
push_ivar 13
push_int 0
identical
jump_if_false L0340
push_ivar 12
send.b 0 idx:40
pop
push_self
push_false
send.b 1 idx:41
push_true
identical
jump_if_false L0321
push_const.b idx:0
push_int 24
send.b 1 idx:2
pop
push_false
store_temp 3
jump L033d
L0321: push_const.b idx:0
push_int 23
send.b 1 idx:2
pop
push_ivar 10
send.b 0 idx:55
store_ivar 13
push_ivar 12
send.b 0 idx:42
pop
push_self
push_int 3
send.b 1 idx:10
pop
L033d: jump L03e3
L0340: push_ivar 13
push_ivar 10
send 0 #slots
push_int 1
op +
identical
jump_if_false L038c
push_ivar 12
send.b 0 idx:40
pop
push_self
push_true
send.b 1 idx:41
push_true
identical
jump_if_false L036d
push_const.b idx:0
push_int 19
send.b 1 idx:2
pop
push_self
push_int 30
send.b 1 idx:10
pop
push_true
store_temp 3
jump L0389
L036d: push_const.b idx:0
push_int 23
send.b 1 idx:2
pop
push_ivar 10
send.b 0 idx:54
store_ivar 13
push_ivar 12
send.b 0 idx:42
pop
push_self
push_int 3
send.b 1 idx:10
pop
L0389: jump L03e3
L038c: push_ivar 13
push_ivar 10
send 0 #fieldN
push_int 1
op +
op <
jump_if_false L03bd
push_ivar 15
push_nil
not_identical
jump_if_false L03ba
push_const.b idx:0
push_ivar 15
push_int 2
op /
push_int 1
op +
push_const.b idx:56
push_ivar 15
push_int 2
op %
at
push_ivar 15
push_int 2
op /
at
send.b 2 idx:57
pop
push_nil
store_ivar 15
L03ba: jump L03e3
L03bd: push_ivar 16
push_nil
not_identical
jump_if_false L03e3
push_const.b idx:0
push_ivar 16
push_int 2
op /
push_int 1
op +
push_const.b idx:58
push_ivar 16
push_int 2
op %
at
push_ivar 16
push_int 2
op /
at
send.b 2 idx:57
pop
push_nil
store_ivar 16
L03e3: push_self
push_int 1
send.b 1 idx:10
pop
jump L014f
L03ed: push_temp 3
push_true
identical
jump_if_false L0420
push_ivar 9
push_int 0
identical
jump_if_false L0415
push_const.b idx:23
push_ivar 10
send.b 0 idx:59
send.b 1 idx:60
pop
push_const.b idx:23
push_ivar 10
send.b 0 idx:61
send.b 1 idx:62
pop
jump L0420
L0415: push_const.b idx:27
push_ivar 10
send.b 0 idx:63
send.b 1 idx:64
pop
L0420: push_const.b idx:0
push_int 16
send.b 1 idx:2
pop
push_ivar 6
send.b 0 idx:65
pop
push_ivar 7
send.b 0 idx:65
pop
push_ivar 8
send.b 0 idx:65
pop
push_ivar 11
send.b 0 idx:65
pop
push_ivar 10
send.b 0 idx:65
pop
push_ivar 12
send.b 0 idx:65
pop
push_self
push_int 15
send.b 1 idx:10
pop
push_ivar 11
send.b 0 idx:14
pop
push_ivar 10
send.b 0 idx:14
pop
push_ivar 12
send.b 0 idx:14
pop
push_ivar 6
send.b 0 idx:14
pop
push_ivar 7
send.b 0 idx:14
pop
push_ivar 8
send.b 0 idx:14
pop
push_const.b idx:66
send.b 0 idx:67
pop
push_self
push_int 1
send.b 1 idx:10
pop
push_temp 3
return_top
return_self
