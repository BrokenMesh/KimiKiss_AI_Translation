; target: LogLine initialize argc=4 table=methods
; original-sha1: db6057e8a5bb5930f84cd4b53e0d45a30d07e13d (292 bytes)
; reason: in the backlog the English plate ran into the text (Aihara + text with no gap) and continuation lines were
;   indented by (plate length + 1) cells. The text now starts at the message window's column: 115 px, or 6 px
;   after a wider plate, and continuation lines at 115 px, so the build's line breaks fit here too. Lines without
;   a plate are unchanged. D-027.
; temps: 0 posX, 1 posY, 2 line index, 3 {cnum, clut, plate, text}; 4 is free until the StringStream below
push_nils 2
push_temp 3
push_int 1
at
store_ivar 0
push_temp 0
store_classvar.b idx:9 4
push_temp 1
store_classvar.b idx:9 5
push_const.b idx:31
store_classvar.b idx:9 6
push_const.b idx:18
push_temp 2
op *
push_const.b idx:32
op +
push_const.b idx:33
op -
store_classvar.b idx:9 7
push_const.b idx:34
store_classvar.b idx:9 8
push_classvar.b idx:9 6
store_classvar.b idx:9 13
push_const.b idx:8
push_int 2
at
push_int 0
at
store_classvar.b idx:9 11
push_const.b idx:8
push_int 2
at
push_int 1
at
store_classvar.b idx:9 12
push_temp 3
push_int 2
at
store_classvar.b idx:9 10
push_const.b idx:35
push_int 80
send.b 1 idx:22
store_ivar 3
push_int 1
store_ivar 4
push_temp 3
push_int 3
at
push_nil
not_identical
jump_if_false.l L0081
push_self
push_temp 3
push_int 3
at
send.b 1 idx:13
pop
; text column after the plate, as in the message window (D-023): 115 px from the line start
; (curX -161), or 6 px after a wider plate; continuation lines at indent 5 cells = 115 px
push_classvar class:LogLine 6
push_const float:6.0
op +
store_temp 4
push_temp 4
push_const float:-161.0
op <
jump_if_false wide
push_const float:-161.0
store_temp 4
wide:
push_temp 4
store_classvar class:LogLine 6
push_int 5
store_classvar class:LogLine 9
jump.l L0086
L0081: push_int 0
store_classvar.b idx:9 9
L0086: push_const.b idx:36
push_temp 3
push_int 0
at
send.b 1 idx:22
store_temp 4
push_temp 4
send.b 0 idx:1
store_temp 5
L0099: push_temp 5
push_nil
not_identical
jump_if_false.l L0110
push_temp 5
push_const.b idx:4
op <
jump_if_false.l L00f0
push_temp 5
push_int 86
identical
jump_if_false.l L00ba
push_self
push_temp 4
send.b 1 idx:37
pop
jump.l L00ed
L00ba: push_temp 5
push_int 84
identical
jump_if_false.l L00cc
push_self
push_temp 4
send.b 1 idx:38
pop
jump.l L00ed
L00cc: push_temp 5
push_int 78
identical
jump_if_false.l L00de
push_self
push_temp 4
send.b 1 idx:39
pop
jump.l L00ed
L00de: push_temp 5
push_int 82
identical
jump_if_false.l L00ed
push_self
push_temp 4
send.b 1 idx:40
pop
L00ed: jump.l L0107
L00f0: push_temp 5
push_const.b idx:41
identical
jump_if_false.l L0100
push_self
send.b 0 idx:19
pop
jump.l L0107
L0100: push_self
push_temp 5
send.b 1 idx:28
pop
L0107: push_temp 4
send.b 0 idx:1
store_temp 5
jump.s L0099
L0110: push_const.b idx:18
push_temp 2
op *
push_const.b idx:18
push_ivar 4
op *
push_int 2
op /
op +
push_const.b idx:33
op -
store_ivar 5
return_self

