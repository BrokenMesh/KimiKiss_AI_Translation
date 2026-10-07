; target: NameEntry selectChar argc=1 table=methods
; original-sha1: b1589d129b7eb10ac4e028ce056c487a01614b89 (695 bytes)
; reason: the name entry has 2N+1 = 17 cursor positions in player mode: the confirm button index 7 becomes `edit slots + 1`
; (moveCursor: and the curX test) and the surname/given-name boundary 4 becomes `edit fieldN + 1` (selects the voice
; clip of the field the cursor leaves). D-016.
push_nils 3
push_ivar 11
send.b 0 idx:42
pop
push_self
push_int 3
send.b 1 idx:10
pop
L000f: push_temp 3
push_nil
identical
jump_if_false L02ad
push_const.b idx:11
send.b 0 idx:12
push_const.b idx:38
op &
push_int 0
not_identical
jump_if_false L0065
push_ivar 10
push_ivar 10
send 0 #slots
push_int 1
op +
send.b 1 idx:39
pop
push_self
push_true
send.b 1 idx:41
push_true
identical
jump_if_false L004b
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
jump L0062
L004b: push_const.b idx:0
push_int 23
send.b 1 idx:2
pop
push_ivar 10
push_ivar 13
send.b 1 idx:39
pop
push_self
push_int 3
send.b 1 idx:10
pop
L0062: jump L01cc
L0065: push_const.b idx:11
send.b 0 idx:12
push_int 32
op &
push_int 0
not_identical
jump_if_false L00cc
push_ivar 11
send.b 0 idx:68
store_temp 2
push_temp 2
push_nil
not_identical
jump_if_false L00c1
push_temp 2
push_const.b idx:69
not_identical
push_temp 0
push_int 0
identical
and
push_temp 1
push_nil
identical
and
jump_if_false L00ad
push_const.b idx:0
push_int 35
send.b 1 idx:2
pop
push_ivar 11
push_int 0
push_temp 2
send.b 2 idx:53
pop
push_int 0
store_temp 1
jump L00be
L00ad: push_const.b idx:0
push_int 17
send.b 1 idx:2
pop
push_ivar 10
push_temp 2
send.b 1 idx:70
store_ivar 13
L00be: jump L00c9
L00c1: push_const.b idx:0
push_int 21
send.b 1 idx:2
pop
L00c9: jump L01cc
L00cc: push_const.b idx:11
send.b 0 idx:12
push_int 64
op &
push_int 0
not_identical
jump_if_false L00fd
push_const.b idx:0
push_int 23
send.b 1 idx:2
pop
push_temp 1
push_nil
not_identical
jump_if_false L00f7
push_ivar 11
push_int 0
send.b 1 idx:53
pop
push_nil
store_temp 1
jump L00fa
L00f7: jump L02ad
L00fa: jump L01cc
L00fd: push_const.b idx:11
send.b 0 idx:12
push_const.b idx:44
op &
push_int 0
not_identical
jump_if_false L011d
push_const.b idx:0
push_int 24
send.b 1 idx:2
pop
push_ivar 10
send.b 0 idx:45
store_ivar 13
jump L01cc
L011d: push_const.b idx:11
send.b 0 idx:46
push_const.b idx:71
op &
push_int 0
not_identical
jump_if_false L0189
push_const.b idx:0
push_int 12
send.b 1 idx:2
pop
push_const.b idx:11
send.b 0 idx:46
push_const.b idx:48
op &
push_int 0
not_identical
jump_if_false L014a
push_ivar 11
send.b 0 idx:49
pop
jump L015e
L014a: push_const.b idx:11
send.b 0 idx:46
push_const.b idx:50
op &
push_int 0
not_identical
jump_if_false L015e
push_ivar 11
send.b 0 idx:51
pop
L015e: push_const.b idx:11
send.b 0 idx:46
push_const.b idx:72
op &
push_int 0
not_identical
jump_if_false L0175
push_ivar 11
send.b 0 idx:54
pop
jump L0189
L0175: push_const.b idx:11
send.b 0 idx:46
push_const.b idx:73
op &
push_int 0
not_identical
jump_if_false L0189
push_ivar 11
send.b 0 idx:55
pop
L0189: push_const.b idx:11
send.b 0 idx:46
push_int 15
op &
push_int 0
not_identical
jump_if_false L01cc
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
jump_if_false L01b7
push_ivar 10
send.b 0 idx:54
store_ivar 13
jump L01cc
L01b7: push_const.b idx:11
send.b 0 idx:46
push_int 10
op &
push_int 0
not_identical
jump_if_false L01cc
push_ivar 10
send.b 0 idx:55
store_ivar 13
L01cc: push_temp 3
push_nil
identical
jump_if_false L02a3
push_ivar 13
push_int 0
identical
jump_if_false L020c
push_self
push_false
send.b 1 idx:41
push_true
identical
jump_if_false L01f3
push_const.b idx:0
push_int 24
send.b 1 idx:2
pop
push_false
store_temp 3
jump L0209
L01f3: push_const.b idx:0
push_int 23
send.b 1 idx:2
pop
push_ivar 10
send.b 0 idx:55
store_ivar 13
push_self
push_int 3
send.b 1 idx:10
pop
L0209: jump L02a3
L020c: push_ivar 13
push_ivar 10
send 0 #slots
push_int 1
op +
identical
jump_if_false L024c
push_self
push_true
send.b 1 idx:41
push_true
identical
jump_if_false L0233
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
jump L0249
L0233: push_const.b idx:0
push_int 23
send.b 1 idx:2
pop
push_ivar 10
send.b 0 idx:54
store_ivar 13
push_self
push_int 3
send.b 1 idx:10
pop
L0249: jump L02a3
L024c: push_ivar 13
push_ivar 10
send 0 #fieldN
push_int 1
op +
op <
jump_if_false L027d
push_ivar 15
push_nil
not_identical
jump_if_false L027a
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
L027a: jump L02a3
L027d: push_ivar 16
push_nil
not_identical
jump_if_false L02a3
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
L02a3: push_self
push_int 1
send.b 1 idx:10
pop
jump L000f
L02ad: push_ivar 11
send.b 0 idx:40
pop
push_temp 3
return_top
return_self
