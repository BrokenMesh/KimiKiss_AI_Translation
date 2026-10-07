; add: NameEntryEdit getStr argc=2 table=methods
; reason: new method. The name in slots from..to-1: leading and trailing blanks (0x8140 or the English space 0x8540) are
; dropped, an inner blank becomes the English space 0x8540. Empty string if nothing is left. D-016.
push_nils 5
push_const ""
store_temp 2
push_temp 0
store_temp 3
push_true
store_temp 6
Lwh7:
push_temp 6
jump_if_false Lend7
push_temp 3
push_temp 1
op <
jump_if_false Lelse8
push_ivar 14
push_temp 3
at
push_const int:0x8140
identical
push_ivar 14
push_temp 3
at
push_const int:0x8540
identical
or
jump_if_false Lelse9
push_temp 3
push_int 1
op +
store_temp 3
jump Lend9
Lelse9:
push_false
store_temp 6
Lend9:
jump Lend8
Lelse8:
push_false
store_temp 6
Lend8:
jump Lwh7
Lend7:
push_temp 1
push_int 1
op -
store_temp 4
push_true
store_temp 6
Lwh10:
push_temp 6
jump_if_false Lend10
push_temp 4
push_temp 3
op >=
jump_if_false Lelse11
push_ivar 14
push_temp 4
at
push_const int:0x8140
identical
push_ivar 14
push_temp 4
at
push_const int:0x8540
identical
or
jump_if_false Lelse12
push_temp 4
push_int 1
op -
store_temp 4
jump Lend12
Lelse12:
push_false
store_temp 6
Lend12:
jump Lend11
Lelse11:
push_false
store_temp 6
Lend11:
jump Lwh10
Lend10:
Lwh13:
push_temp 3
push_temp 4
op <=
jump_if_false Lend13
push_ivar 14
push_temp 3
at
store_temp 5
push_temp 5
push_const int:0x8140
identical
push_temp 5
push_const int:0x8540
identical
or
jump_if_false Lend14
push_const int:0x8540
store_temp 5
Lend14:
push_temp 2
push_temp 5
send 0 #asChar
op +
store_temp 2
push_temp 3
push_int 1
op +
store_temp 3
jump Lwh13
Lend13:
push_temp 2
return_top
return_self
