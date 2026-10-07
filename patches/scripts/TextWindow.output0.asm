; target: TextWindow output argc=0 table=methods
; original-sha1: 6891c1cf1521f1ea9f0161976100108661c4d836 (231 bytes)
; reason: command 7 (putIndent, sent only by Parson>>message: right after the speaker plate) also moves curX, so the
; first line of a spoken line starts at the same column as the continuation lines instead of directly after the
; plate (English plates have no trailing blank; Japanese relied on the hanging bracket). Plate wider than the indent:
; 6 px gap. D-023.
; D-029: the wait after each printed character (waitCnt = putWait) is halved. English lines have roughly 1.5-2x the
; characters of the Japanese ones; the loop spends waitCnt+1 frames per character, so every speed step is at least 1.5x faster.
push_nils 2
push_ivar 20
send.b 0 idx:46
store_temp 0
push_temp 0
push_const.b idx:47
op >
jump_if_false.l L001f
push_self
push_temp 0
send.b 1 idx:50
pop
push_ivar 14
push_const float:0.5
op *
store_ivar 30
jump.l L00e6
L001f: push_temp 0
push_int 5
identical
jump_if_false.l L002f
push_self
send.b 0 idx:51
pop
jump.l L00e6
L002f: push_temp 0
push_int 6
identical
jump_if_false.l L0041
push_ivar 20
send.b 0 idx:46
store_ivar 30
jump.l L00e6
L0041: push_temp 0
push_int 2
identical
jump_if_false.l L0053
push_ivar 20
send.b 0 idx:46
store_ivar 14
jump.l L00e6
L0053: push_temp 0
push_int 0
identical
jump_if_false.l L0079
push_ivar 20
send.b 0 idx:46
store_temp 1
push_const.b idx:4
push_temp 1
at
push_int 0
at
store_ivar 11
push_const.b idx:4
push_temp 1
at
push_int 1
at
store_ivar 12
jump.l L00e6
L0079: push_temp 0
push_int 1
identical
jump_if_false.l L008b
push_ivar 20
send.b 0 idx:46
store_ivar 16
jump.l L00e6
L008b: push_temp 0
push_int 3
identical
jump_if_false.l L00a3
push_const.b idx:5
push_ivar 20
send.b 0 idx:46
at
push_const.b idx:6
op *
store_ivar 17
jump.l L00e6
L00a3: push_temp 0
push_int 12
identical
jump_if_false.l L00b2
push_ivar 32
store_ivar 35
jump.l L00e6
L00b2: push_temp 0
push_int 13
identical
jump_if_false.l L00c7
push_self
push_ivar 20
send.b 0 idx:46
send.b 1 idx:52
pop
jump.l L00e6
L00c7: push_temp 0
push_int 7
identical
jump_if_false.l L00d9
push_ivar 20
send.b 0 idx:46
store_ivar 34
; English plate gap: line 1 starts at the indent column (posX + marginX + indent*(fontW+pitchX)),
; or 6 px after the plate when the plate is wider. Only Parson>>message: sends command 7, after a plate.
push_ivar 34
push_int 0
op >
jump_if_false L00e6
push_ivar 1
push_ivar 5
op +
push_ivar 34
push_ivar 9
push_ivar 7
op +
op *
op +
push_ivar 32
push_int 6
op +
op >
jump_if_false Lgap
push_ivar 1
push_ivar 5
op +
push_ivar 34
push_ivar 9
push_ivar 7
op +
op *
op +
store_ivar 32
jump L00e6
Lgap: push_ivar 32
push_int 6
op +
store_ivar 32
jump.l L00e6
L00d9: push_temp 0
push_int 8
identical
jump_if_false.l L00e6
push_self
send.b 0 idx:53
pop
L00e6: return_self
