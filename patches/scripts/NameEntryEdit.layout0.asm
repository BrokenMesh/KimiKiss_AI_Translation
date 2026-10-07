; add: NameEntryEdit layout argc=0 table=methods
; reason: new method. Places every name slot. Per field the natural width is the sum of the slot advances (adv:, empty
; slots emptyW); the scale is s = min(1, fieldW / width) of the widest field, shared by all fields, so 8 narrow letters, 8 capital Ws or 8 full-width
; Japanese characters all fit their field without overlap. Slot i is drawn left to right: glyph scaled by s and
; centred at left + 12 s with a constant baseline (y = -169 + 9 s), underline `waku` centred and stretched to the
; slot advance, highlight cursor moved and stretched when slot i is the current one. D-016.
push_nils 13
push_self
send 0 #fieldN
store_temp 0
push_self
send 0 #slots
push_temp 0
op /
store_temp 1
push_self
send 0 #fieldW
store_temp 12
push_const float:1.0
store_temp 6
push_int 0
store_temp 2
Lwh19:
push_temp 2
push_temp 1
op <
jump_if_false Lend19
push_temp 2
push_temp 0
op *
store_temp 3
push_const float:0.0
store_temp 4
push_int 0
store_temp 5
Lwh20:
push_temp 5
push_temp 0
op <
jump_if_false Lend20
push_temp 4
push_self
push_ivar 14
push_temp 3
push_temp 5
op +
at
send 1 #adv
op +
store_temp 4
push_temp 5
push_int 1
op +
store_temp 5
jump Lwh20
Lend20:
push_temp 4
push_temp 12
op >
push_temp 12
push_temp 4
op /
push_temp 6
op <
and
jump_if_false Lend21
push_temp 12
push_temp 4
op /
store_temp 6
Lend21:
push_temp 2
push_int 1
op +
store_temp 2
jump Lwh19
Lend19:
push_int 0
store_temp 2
Lwh22:
push_temp 2
push_temp 1
op <
jump_if_false Lend22
push_temp 2
push_temp 0
op *
store_temp 3
push_self
push_temp 2
send 1 #fieldL
store_temp 7
push_int 0
store_temp 5
Lwh23:
push_temp 5
push_temp 0
op <
jump_if_false Lend23
push_temp 3
push_temp 5
op +
store_temp 9
push_self
push_ivar 14
push_temp 9
at
send 1 #adv
store_temp 8
push_ivar 13
push_temp 9
at
store_temp 10
push_temp 10
push_temp 6
push_temp 6
send 2 #setScale
pop
push_temp 10
push_temp 7
push_const float:12.0
push_temp 6
op *
op +
push_const float:-169.0
push_const float:9.0
push_temp 6
op *
op +
send 2 #setPos
pop
push_ivar 2
push_temp 9
at
store_temp 11
push_temp 11
push_temp 7
push_temp 8
push_temp 6
op *
push_const float:0.5
op *
op +
push_const float:-144.0
send 2 #setPos
pop
push_temp 11
push_temp 8
push_temp 6
op *
push_const float:1.0
op +
push_const float:24.0
op /
push_const float:1.0
send 2 #setScale
pop
push_ivar 11
push_int 1
op -
push_temp 9
identical
jump_if_false Lend24
push_ivar 10
push_temp 7
push_temp 8
push_temp 6
op *
push_const float:0.5
op *
op +
push_const float:-160.0
push_int 1
push_const float:3.0
send 4 #move
pop
push_ivar 10
push_temp 8
push_temp 6
op *
push_const float:4.0
op +
push_const float:25.0
op /
push_const float:1.0
push_int 1
push_const float:3.0
send 4 #zoom
pop
Lend24:
push_temp 7
push_temp 8
push_temp 6
op *
op +
store_temp 7
push_temp 5
push_int 1
op +
store_temp 5
jump Lwh23
Lend23:
push_temp 2
push_int 1
op +
store_temp 2
jump Lwh22
Lend22:
return_self
