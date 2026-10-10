; target: MainMenu scriptMain argc=0 table=methods
; original-sha1: 6f9c2ae70b9aebdb0a31b6b968e3c5edb6eaf5b1
; reason: Easy mode (D-038): circle on command 6 opens the Easy Mode panel (Configuration easyMode: 0),
;   built like the Settings branch before it. The rest is the original method (scfasm listing).
push_nils 9
push_const.b idx:0
push_int 33
send.b 1 idx:1
pop
push_self
send.b 0 idx:2
pop
push_classvar.b idx:3 4
push_const.b idx:4
send.b 1 idx:5
pop
push_const.b idx:6
send.b 0 idx:7
store_temp 0
push_classvar.b idx:3 5
push_const.b idx:8
push_temp 0
push_int 4
op /
push_int 1
op +
push_temp 0
push_int 4
op %
send.b 3 idx:9
pop
push_self
send.b 0 idx:10
pop
push_const.b idx:0
push_int 33
send.b 1 idx:11
pop
push_classvar.b idx:3 5
push_const.b idx:8
push_temp 0
push_int 4
op /
push_int 1
op +
push_temp 0
push_int 4
op %
push_int 1
push_const.b idx:12
send.b 5 idx:13
send.b 0 idx:14
pop
push_self
push_int 15
send.b 1 idx:15
pop
push_const.b idx:16
push_const.b idx:17
push_int 0
push_int 8
send.b 3 idx:18
push_const.b idx:4
send.b 1 idx:19
push_const.b idx:20
push_const.b idx:21
send.b 2 idx:22
store_temp 1
push_temp 1
push_const.b idx:23
push_int 2
push_const.b idx:24
send.b 3 idx:25
push_const.b idx:26
push_const.b idx:21
push_int 1
push_const.b idx:24
send.b 4 idx:27
pop
push_self
push_int 9
send.b 1 idx:15
pop
push_const.b idx:28
push_int 12
push_const.b idx:29
push_const.b idx:30
push_int 0
push_int 1
send.b 5 idx:18
store_temp 2
push_const.b idx:28
push_int 12
push_const.b idx:31
push_const.b idx:32
push_int 1
push_int 2
send.b 5 idx:18
store_temp 3
push_self
send.b 0 idx:33
pop
push_ivar 2
push_int 2
send.b 1 idx:34
pop
push_self
push_int 12
send.b 1 idx:15
pop
push_temp 2
send.b 0 idx:34
pop
push_self
push_int 3
send.b 1 idx:15
pop
push_temp 3
send.b 0 idx:34
pop
push_self
push_int 3
send.b 1 idx:15
pop
push_int 0
store_temp 4
L00f1: push_true
jump_if_false.l L0524
push_int 0
push_const.b idx:35
push_const.b idx:36
send.b 1 idx:37
op -
store_temp 5
push_const.b idx:38
send.b 0 idx:39
push_int 32
op &
push_int 0
not_identical
jump_if_false.l L047e
push_temp 2
send.b 0 idx:40
pop
push_temp 3
send.b 0 idx:40
pop
push_ivar 3
push_ivar 1
at
store_temp 6
push_temp 6
push_int 0
identical
jump_if_false.l L0216
push_const.b idx:0
push_int 18
send.b 1 idx:41
pop
push_ivar 2
push_int 2
send.b 1 idx:40
pop
push_temp 1
push_const.b idx:4
push_int 1
push_const.b idx:24
send.b 3 idx:25
push_const.b idx:20
push_const.b idx:21
push_int 2
push_const.b idx:24
send.b 4 idx:27
pop
push_self
push_int 30
send.b 1 idx:15
pop
push_classvar.b idx:3 5
push_int 74
push_int 1
push_int 0
push_int 1
push_const.b idx:12
send.b 5 idx:13
pop
push_self
push_int 30
send.b 1 idx:15
pop
push_const.b idx:42
send.b 0 idx:18
push_int 0
send.b 1 idx:43
store_temp 7
push_self
push_int 9
send.b 1 idx:15
pop
push_temp 7
push_true
identical
jump_if_false.l L01c5
push_classvar.b idx:3 6
send.b 0 idx:44
pop
push_classvar.b idx:3 9
push_const.b idx:45
send.b 1 idx:46
store_temp 7
push_classvar.b idx:3 6
send.b 0 idx:47
pop
push_classvar.b idx:3 6
send.b 0 idx:48
pop
push_temp 7
push_int 0
identical
jump_if_false.l L01bc
push_const.b idx:49
push_int 1
send.b 1 idx:18
throw
jump.l L01c5
L01bc: push_const.b idx:49
push_int 1
push_true
send.b 2 idx:18
throw
L01c5: push_classvar.b idx:3 5
push_const.b idx:8
push_temp 0
push_int 4
op /
push_int 1
op +
push_temp 0
push_int 4
op %
push_int 1
push_const.b idx:12
send.b 5 idx:13
pop
push_self
push_int 15
send.b 1 idx:15
pop
push_temp 1
push_const.b idx:23
push_int 2
push_const.b idx:24
send.b 3 idx:25
push_const.b idx:26
push_const.b idx:21
push_int 1
push_const.b idx:24
send.b 4 idx:27
pop
push_self
push_int 9
send.b 1 idx:15
pop
push_ivar 2
push_int 2
send.b 1 idx:34
pop
push_self
push_int 12
send.b 1 idx:15
pop
jump.l L0461
L0216: push_temp 6
push_int 1
identical
jump_if_false.l L0297
push_const.b idx:0
push_int 17
send.b 1 idx:41
pop
push_temp 1
push_const.b idx:4
push_int 1
push_const.b idx:24
send.b 3 idx:25
push_const.b idx:20
push_const.b idx:21
push_int 2
push_const.b idx:24
send.b 4 idx:27
pop
push_ivar 2
push_int 2
send.b 1 idx:40
pop
push_self
push_int 21
send.b 1 idx:15
pop
push_classvar.b idx:3 8
push_const.b idx:4
send.b 1 idx:44
pop
push_const.b idx:50
send.b 0 idx:18
send.b 0 idx:43
pop
push_classvar.b idx:3 8
push_const.b idx:4
send.b 1 idx:48
pop
push_temp 1
push_const.b idx:23
push_int 2
push_const.b idx:24
send.b 3 idx:25
push_const.b idx:26
push_const.b idx:21
push_int 1
push_const.b idx:24
send.b 4 idx:27
pop
push_self
push_int 9
send.b 1 idx:15
pop
push_ivar 2
push_int 2
send.b 1 idx:34
pop
push_self
push_int 12
send.b 1 idx:15
pop
jump.l L0461
L0297: push_temp 6
push_int 2
identical
jump_if_false.l L0318
push_const.b idx:0
push_int 17
send.b 1 idx:41
pop
push_ivar 2
push_int 2
send.b 1 idx:40
pop
push_self
push_int 18
send.b 1 idx:15
pop
push_const.b idx:51
send.b 0 idx:18
send.b 0 idx:43
jump_if_false.l L02ff
push_temp 0
push_const.b idx:6
send.b 0 idx:7
not_identical
jump_if_false.l L02f4
push_const.b idx:6
send.b 0 idx:7
store_temp 0
push_classvar.b idx:3 5
push_const.b idx:8
push_temp 0
push_int 4
op /
push_int 1
op +
push_temp 0
push_int 4
op %
push_int 1
push_const.b idx:12
send.b 5 idx:13
pop
push_self
push_int 15
send.b 1 idx:15
pop
L02f4: push_ivar 2
send.b 0 idx:52
pop
push_self
send.b 0 idx:33
pop
L02ff: push_self
push_int 9
send.b 1 idx:15
pop
push_ivar 2
push_int 2
send.b 1 idx:34
pop
push_self
push_int 12
send.b 1 idx:15
pop
jump.l L0461
L0318: push_temp 6
push_int 3
identical
jump_if_false.l L03bd
push_const.b idx:0
push_int 18
send.b 1 idx:41
pop
push_const.b idx:0
send.b 0 idx:53
pop
push_const.b idx:54
send.b 0 idx:18
send.b 0 idx:55
store_temp 8
push_ivar 2
push_int 2
send.b 1 idx:40
pop
push_temp 1
push_const.b idx:4
push_int 1
push_const.b idx:24
send.b 3 idx:25
push_const.b idx:20
push_const.b idx:21
push_int 2
push_const.b idx:24
send.b 4 idx:27
pop
push_self
push_int 45
send.b 1 idx:15
pop
push_temp 8
send.b 0 idx:43
pop
push_const.b idx:0
push_int 33
send.b 1 idx:11
pop
push_classvar.b idx:3 5
push_const.b idx:8
push_temp 0
push_int 4
op /
push_int 1
op +
push_temp 0
push_int 4
op %
push_int 1
push_const.b idx:12
send.b 5 idx:13
pop
push_self
push_int 15
send.b 1 idx:15
pop
push_temp 1
push_const.b idx:23
push_int 2
push_const.b idx:24
send.b 3 idx:25
push_const.b idx:26
push_const.b idx:21
push_int 1
push_const.b idx:24
send.b 4 idx:27
pop
push_self
push_int 9
send.b 1 idx:15
pop
push_ivar 2
push_int 2
send.b 1 idx:34
pop
push_self
push_int 12
send.b 1 idx:15
pop
jump.l L0461
L03bd: push_temp 6
push_int 4
identical
jump_if_false.l L042c
push_const.b idx:0
push_int 18
send.b 1 idx:41
pop
push_ivar 2
push_int 2
send.b 1 idx:40
pop
push_temp 1
push_const.b idx:4
push_int 1
push_const.b idx:24
send.b 3 idx:25
push_const.b idx:20
push_const.b idx:21
push_int 2
push_const.b idx:24
send.b 4 idx:27
pop
push_self
push_int 45
send.b 1 idx:15
pop
push_const.b idx:56
send.b 0 idx:18
send.b 0 idx:43
pop
push_temp 1
push_const.b idx:23
push_int 2
push_const.b idx:24
send.b 3 idx:25
push_const.b idx:26
push_const.b idx:21
push_int 1
push_const.b idx:24
send.b 4 idx:27
pop
push_self
push_int 9
send.b 1 idx:15
pop
push_ivar 2
push_int 2
send.b 1 idx:34
pop
push_self
push_int 12
send.b 1 idx:15
pop
jump.l L0461
L042c: push_temp 6
push_int 5
identical
jump_if_false.l easy
push_const.b idx:0
push_int 35
send.b 1 idx:41
pop
push_ivar 2
send.b 0 idx:5
pop
push_const.b idx:57
send.b 0 idx:18
push_int 0
send.b 1 idx:43
pop
push_const.b idx:6
send.b 0 idx:7
store_temp 0
push_ivar 2
send.b 0 idx:58
pop
push_self
push_int 3
send.b 1 idx:15
pop
jump.l L0461                ; new: end of the Settings branch
easy: push_temp 6            ; new: command 6, Easy Mode (D-038)
push_int 6
identical
jump_if_false.l L0461
push_const class:Sound
push_int 35
send 1 #playSE
pop
push_ivar 2
send 0 #disable
pop
push_const class:Configuration
send 0 #new
push_int 0
send 1 #easyMode
pop
push_ivar 2
send 0 #enable
pop
push_self
push_int 3
send 1 #sleep
pop
L0461: push_temp 2
send.b 0 idx:34
pop
push_self
push_int 3
send.b 1 idx:15
pop
push_temp 3
send.b 0 idx:34
pop
push_self
push_int 3
send.b 1 idx:15
pop
jump.l L051a
L047e: push_const.b idx:38
send.b 0 idx:39
push_int 64
op &
push_int 0
not_identical
jump_if_false.l L04b3
push_const.b idx:0
push_int 24
send.b 1 idx:41
pop
push_ivar 3
push_ivar 1
at
push_int 5
identical
jump_if_false.l L04a6
push_classvar.b idx:3 4
send.b 0 idx:40
pop
L04a6: push_self
push_int 1
send.b 1 idx:15
pop
jump.l L0524
jump.l L051a
L04b3: push_const.b idx:38
send.b 0 idx:59
push_const.b idx:60
op &
push_int 0
not_identical
jump_if_false.l L051a
push_const.b idx:0
push_int 13
send.b 1 idx:41
pop
push_ivar 3
push_ivar 1
at
push_int 5
identical
jump_if_false.l L04db
push_classvar.b idx:3 4
send.b 0 idx:40
pop
L04db: push_const.b idx:38
send.b 0 idx:59
push_const.b idx:61
op &
push_int 0
not_identical
jump_if_false.l L04f3
push_ivar 2
send.b 0 idx:62
store_ivar 1
jump.l L0508
L04f3: push_const.b idx:38
send.b 0 idx:59
push_const.b idx:63
op &
push_int 0
not_identical
jump_if_false.l L0508
push_ivar 2
send.b 0 idx:64
store_ivar 1
L0508: push_ivar 3
push_ivar 1
at
push_int 5
identical
jump_if_false.l L051a
push_classvar.b idx:3 4
send.b 0 idx:34
pop
L051a: push_self
push_int 1
send.b 1 idx:15
pop
jump.l L00f1
L0524: push_const.b idx:35
push_temp 5
send.b 1 idx:37
pop
push_ivar 2
push_int 2
send.b 1 idx:40
pop
push_temp 2
send.b 0 idx:40
pop
push_temp 3
send.b 0 idx:40
pop
push_self
push_int 21
send.b 1 idx:15
pop
push_ivar 2
send.b 0 idx:52
pop
push_temp 2
send.b 0 idx:52
pop
push_temp 3
send.b 0 idx:52
pop
push_temp 1
push_const.b idx:4
push_int 1
push_const.b idx:24
send.b 3 idx:25
push_const.b idx:20
push_const.b idx:21
push_int 2
push_const.b idx:24
send.b 4 idx:27
pop
push_const.b idx:0
send.b 0 idx:53
pop
push_classvar.b idx:3 5
push_int 2
push_const.b idx:65
send.b 2 idx:53
send.b 0 idx:14
pop
push_temp 1
send.b 0 idx:52
pop
push_const.b idx:66
send.b 0 idx:67
pop
push_self
push_int 1
send.b 1 idx:15
pop
return_self
